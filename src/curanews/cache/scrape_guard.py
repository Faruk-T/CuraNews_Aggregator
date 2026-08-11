"""Scrape lock and cooldown helpers — IMPLEMENTATION_PLAN §6.5."""

from __future__ import annotations

import logging

from curanews.cache.redis_client import RedisClient, get_redis_client

logger = logging.getLogger(__name__)

DEFAULT_LOCK_TTL_SECONDS = 300
DEFAULT_COOLDOWN_TTL_SECONDS = 120
_LOCK_VALUE = "1"
_COOLDOWN_VALUE = "1"


def scrape_lock_key(source_id: str) -> str:
    return f"scrape:lock:{source_id}"


def scrape_cooldown_key(source_id: str) -> str:
    return f"scrape:cooldown:{source_id}"


class ScrapeGuard:
    """Prevent parallel scrapes and enforce post-429 cooldown windows."""

    def __init__(self, client: RedisClient | None = None) -> None:
        self._client = client or get_redis_client()

    def try_acquire_lock(
        self,
        source_id: str,
        *,
        ttl_seconds: int = DEFAULT_LOCK_TTL_SECONDS,
    ) -> bool:
        """Return True when the caller owns the lock (or Redis is unavailable)."""
        if not self._client.available:
            logger.warning(
                "scrape lock bypass source_id=%s reason=redis_unavailable",
                source_id,
            )
            return True

        key = scrape_lock_key(source_id)
        acquired = self._client.set(key, _LOCK_VALUE, nx=True, ex=ttl_seconds)
        if acquired:
            logger.info("scrape lock acquired source_id=%s ttl=%s", source_id, ttl_seconds)
        else:
            logger.info("scrape lock busy source_id=%s", source_id)
        return acquired

    def release_lock(self, source_id: str) -> bool:
        if not self._client.available:
            return False
        released = self._client.delete(scrape_lock_key(source_id))
        if released:
            logger.info("scrape lock released source_id=%s", source_id)
        return released

    def set_cooldown(
        self,
        source_id: str,
        *,
        ttl_seconds: int = DEFAULT_COOLDOWN_TTL_SECONDS,
    ) -> bool:
        if not self._client.available:
            return False
        key = scrape_cooldown_key(source_id)
        stored = self._client.setex(key, ttl_seconds, _COOLDOWN_VALUE)
        if stored:
            logger.info("scrape cooldown set source_id=%s ttl=%s", source_id, ttl_seconds)
        return stored

    def is_on_cooldown(self, source_id: str) -> bool:
        if not self._client.available:
            return False
        return self._client.exists(scrape_cooldown_key(source_id))
