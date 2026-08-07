"""Polite crawling policy: allowlist, User-Agent, concurrency guard (Issue #10 / G10)."""

from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlparse

from curanews.config import get_settings

DEFAULT_USER_AGENT = "CuraNewsBot/0.1 (+https://github.com/Faruk-T/CuraNews_Aggregator)"


class HostNotAllowedError(ValueError):
    """Raised when a fetch target is outside the configured allowlist."""


def user_agent() -> str:
    return get_settings().scrape_user_agent or DEFAULT_USER_AGENT


@lru_cache(maxsize=1)
def allowed_hosts() -> frozenset[str]:
    raw = get_settings().scrape_allowlist_hosts
    hosts = {part.strip().lower() for part in raw.split(",") if part.strip()}
    return frozenset(hosts)


def is_url_allowed(url: str) -> bool:
    """Return True if ``url`` may be fetched under the host allowlist."""
    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "").lower()
    if scheme == "file":
        return True
    host = (parsed.hostname or "").lower()
    if not host:
        return False
    return host in allowed_hosts()


def assert_url_allowed(url: str) -> None:
    """Fail closed on hosts outside ``SCRAPE_ALLOWLIST_HOSTS``."""
    if is_url_allowed(url):
        return
    host = urlparse(url).hostname or "?"
    allowed = ", ".join(sorted(allowed_hosts()))
    raise HostNotAllowedError(
        f"host {host!r} is not in scrape allowlist ({allowed})"
    )


def assert_concurrency_polite(value: int | None = None) -> int:
    """Resolve worker count; project default remains ``SCRAPE_CONCURRENCY`` (≤ 2)."""
    settings = get_settings()
    if value is None:
        return max(1, settings.scrape_concurrency)
    return max(1, value)


def default_concurrency() -> int:
    """Configured default concurrency (G10: should stay ≤ 2 in dev)."""
    return max(1, get_settings().scrape_concurrency)
