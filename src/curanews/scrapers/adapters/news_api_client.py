"""HTTP news API adapter with backoff and offline fixture (Issue #8)."""

from __future__ import annotations

import logging
from typing import Literal
from urllib.parse import urlencode

import httpx

from curanews.config import get_settings
from curanews.domain.models import RawArticleDraft
from curanews.resilience import BackoffPolicy, call_with_backoff
from curanews.scrapers.adapters.news_api import load_gnews_fixture, parse_gnews_payload

logger = logging.getLogger("curanews.adapters.news_api")


class NewsApiAdapter:
    """Fetch headlines from a GNews-compatible JSON API."""

    source_id = "gnews_api"
    kind: Literal["api"] = "api"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        category: str = "technology",
        base_url: str | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.news_api_key
        self.category = category
        self.base_url = base_url or settings.news_api_base_url

    def fetch(self, *, limit: int = 50) -> list[RawArticleDraft]:
        if not self.api_key:
            logger.info("NEWS_API_KEY missing — using offline gnews_sample.json fixture")
            return load_gnews_fixture()[:limit]

        params = {
            "category": self.category,
            "max": str(min(limit, 100)),
            "apikey": self.api_key,
        }
        url = f"{self.base_url}?{urlencode(params)}"

        def _request() -> dict:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url)
                if response.status_code >= 400:
                    err = RuntimeError(f"HTTP {response.status_code} from news API")
                    err.status_code = response.status_code  # type: ignore[attr-defined]
                    raise err
                return response.json()

        settings = get_settings()
        payload = call_with_backoff(
            _request,
            policy=BackoffPolicy(
                base_seconds=settings.scrape_backoff_base,
                max_retries=settings.scrape_max_retries,
            ),
            source_key=self.source_id,
        )
        drafts = parse_gnews_payload(
            payload,
            source_id=self.source_id,
            default_category=self.category,
        )
        return drafts[:limit]
