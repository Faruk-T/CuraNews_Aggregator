"""Fetch official RSS/Atom feeds with allowlist + backoff (no API key)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Literal

import httpx

from curanews.config import get_settings
from curanews.domain.models import RawArticleDraft
from curanews.resilience import BackoffPolicy, call_with_backoff
from curanews.scrapers.adapters.rss import load_rss_fixture, parse_feed_xml
from curanews.scrapers.adapters.rss_catalog import DEFAULT_RSS_FEEDS, RssFeed
from curanews.scrapers.policy import assert_url_allowed, user_agent

logger = logging.getLogger("curanews.adapters.rss")

HttpGet = Callable[[str], str]


class RssCatalogAdapter:
    """Pull headlines from the documented public RSS catalog.

    Live HTTP is the default (no vendor API key). Tests inject ``http_get``
    or call ``fetch_fixture()`` so CI never depends on the public internet.
    """

    source_id = "rss_catalog"
    kind: Literal["rss"] = "rss"

    def __init__(
        self,
        *,
        feeds: tuple[RssFeed, ...] | None = None,
        http_get: HttpGet | None = None,
        use_fixture: bool = False,
    ) -> None:
        self.feeds = feeds if feeds is not None else DEFAULT_RSS_FEEDS
        self._http_get = http_get
        self.use_fixture = use_fixture

    def fetch(self, *, limit: int = 50) -> list[RawArticleDraft]:
        cap = max(1, limit)
        if self.use_fixture:
            return load_rss_fixture()[:cap]

        buckets: list[list[RawArticleDraft]] = []
        for feed in self.feeds:
            try:
                xml = self._download(feed)
            except Exception as exc:  # noqa: BLE001
                logger.warning("rss fetch failed feed=%s error=%s", feed.key, exc)
                continue
            rows = parse_feed_xml(xml, feed=feed)
            logger.info("rss parsed feed=%s items=%s", feed.key, len(rows))
            if rows:
                buckets.append(rows)

        return _round_robin(buckets, cap)

    def _download(self, feed: RssFeed) -> str:
        assert_url_allowed(feed.url)
        if self._http_get is not None:
            return self._http_get(feed.url)
        return _http_get_xml(feed.url, source_key=feed.key)


def _http_get_xml(url: str, *, source_key: str) -> str:
    settings = get_settings()
    headers = {
        "User-Agent": user_agent(),
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
    }

    def _request() -> str:
        with httpx.Client(timeout=20.0, follow_redirects=True, headers=headers) as client:
            response = client.get(url)
            if response.status_code >= 400:
                err = RuntimeError(f"HTTP {response.status_code} from RSS {url}")
                err.status_code = response.status_code  # type: ignore[attr-defined]
                raise err
            return response.text

    return call_with_backoff(
        _request,
        policy=BackoffPolicy(
            base_seconds=settings.scrape_backoff_base,
            max_retries=settings.scrape_max_retries,
        ),
        source_key=source_key,
    )


def _round_robin(buckets: list[list[RawArticleDraft]], cap: int) -> list[RawArticleDraft]:
    """Take one item from each publisher in turn so BBC cannot fill the whole quota."""
    mixed: list[RawArticleDraft] = []
    index = 0
    while len(mixed) < cap and buckets:
        progressed = False
        for bucket in buckets:
            if index < len(bucket):
                mixed.append(bucket[index])
                progressed = True
                if len(mixed) >= cap:
                    break
        if not progressed:
            break
        index += 1
    return mixed[:cap]
