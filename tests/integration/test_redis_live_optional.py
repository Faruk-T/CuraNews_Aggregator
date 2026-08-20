"""Optional live Redis smoke (skipped unless CURANEWS_REDIS_URL is set)."""

from __future__ import annotations

import os

import pytest

from curanews.cache.feed_cache import CacheOutcome, FeedCache
from curanews.cache.redis_client import RedisClient


@pytest.mark.redis
def test_live_redis_set_get_invalidate() -> None:
    url = os.environ.get("CURANEWS_REDIS_URL") or os.environ.get("REDIS_URL")
    assert url, "marker skip should have fired if unset"

    client = RedisClient(url=url)
    if not client.available:
        pytest.skip("Redis URL set but server not reachable")

    cache = FeedCache(client=client, ttl_seconds=30)
    user_id = "g19-live-redis"
    query = {"limit": 3}
    cache.invalidate(user_id, query)

    miss = cache.get(user_id, query)
    assert miss.outcome == CacheOutcome.MISS

    payload = {"user_id": user_id, "cache": "miss", "items": []}
    assert cache.set(user_id, query, payload) is True

    hit = cache.get(user_id, query)
    assert hit.outcome == CacheOutcome.HIT
    assert hit.payload == payload

    assert cache.invalidate(user_id, query) is True
    assert cache.get(user_id, query).outcome == CacheOutcome.MISS
