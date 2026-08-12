"""Personal feed cache — IMPLEMENTATION_PLAN §6.5 ``feed:{user_id}:{query_hash}``."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from curanews.cache.redis_client import RedisClient, get_redis_client
from curanews.config import get_settings

logger = logging.getLogger(__name__)


class CacheOutcome(str, Enum):
    HIT = "HIT"
    MISS = "MISS"
    BYPASS = "BYPASS"


@dataclass(frozen=True, slots=True)
class FeedCacheResult:
    outcome: CacheOutcome
    payload: Any | None
    key: str


def feed_cache_key(user_id: str, query: dict[str, Any]) -> str:
    """Build a stable Redis key for a user feed query."""
    query_blob = json.dumps(query, sort_keys=True, separators=(",", ":"))
    query_hash = hashlib.sha256(query_blob.encode("utf-8")).hexdigest()[:16]
    return f"feed:{user_id}:{query_hash}"


class FeedCache:
    """Store and retrieve serialized feed payloads with HIT/MISS logging."""

    def __init__(
        self,
        client: RedisClient | None = None,
        *,
        ttl_seconds: int | None = None,
    ) -> None:
        self._client = client or get_redis_client()
        self._ttl = ttl_seconds or get_settings().feed_cache_ttl_seconds

    @property
    def ttl_seconds(self) -> int:
        return self._ttl

    def get(self, user_id: str, query: dict[str, Any]) -> FeedCacheResult:
        key = feed_cache_key(user_id, query)
        if not self._client.available:
            logger.info("cache outcome=BYPASS key=%s reason=redis_unavailable", key)
            return FeedCacheResult(CacheOutcome.BYPASS, None, key)

        raw = self._client.get(key)
        if raw is None:
            logger.info("cache outcome=MISS key=%s", key)
            return FeedCacheResult(CacheOutcome.MISS, None, key)

        logger.info("cache outcome=HIT key=%s", key)
        return FeedCacheResult(CacheOutcome.HIT, json.loads(raw), key)

    def set(self, user_id: str, query: dict[str, Any], payload: Any) -> bool:
        key = feed_cache_key(user_id, query)
        if not self._client.available:
            return False
        raw = json.dumps(payload, separators=(",", ":"))
        stored = self._client.setex(key, self._ttl, raw)
        if stored:
            logger.info("cache stored key=%s ttl=%s", key, self._ttl)
        return stored

    def invalidate(self, user_id: str, query: dict[str, Any]) -> bool:
        key = feed_cache_key(user_id, query)
        if not self._client.available:
            return False
        deleted = self._client.delete(key)
        if deleted:
            logger.info("cache invalidated key=%s", key)
        return deleted

    def invalidate_all(self) -> int:
        """Drop all ``feed:*`` keys after new articles land (G13/G17)."""
        if not self._client.available:
            return 0
        removed = self._client.delete_by_prefix("feed:")
        if removed:
            logger.info("cache invalidated prefix=feed:* count=%s", removed)
        return removed
