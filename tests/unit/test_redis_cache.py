"""Tests for Redis feed cache and scrape guard (Issue #12 / G12)."""

from __future__ import annotations

import time

import pytest

from curanews.cache.feed_cache import CacheOutcome, FeedCache
from curanews.cache.scrape_guard import ScrapeGuard


class FakeRedisClient:
    """In-memory Redis stand-in for unit tests."""

    def __init__(self, *, available: bool = True) -> None:
        self._available = available
        self._store: dict[str, str] = {}
        self._expiry: dict[str, float] = {}

    @property
    def available(self) -> bool:
        return self._available

    def _purge(self, key: str) -> None:
        expires_at = self._expiry.get(key)
        if expires_at is not None and time.monotonic() >= expires_at:
            self._store.pop(key, None)
            self._expiry.pop(key, None)

    def get(self, key: str) -> str | None:
        self._purge(key)
        return self._store.get(key)

    def setex(self, key: str, ttl_seconds: int, value: str) -> bool:
        self._store[key] = value
        self._expiry[key] = time.monotonic() + ttl_seconds
        return True

    def set(
        self,
        key: str,
        value: str,
        *,
        nx: bool = False,
        ex: int | None = None,
    ) -> bool:
        self._purge(key)
        if nx and key in self._store:
            return False
        self._store[key] = value
        if ex is not None:
            self._expiry[key] = time.monotonic() + ex
        return True

    def delete(self, key: str) -> bool:
        existed = key in self._store
        self._store.pop(key, None)
        self._expiry.pop(key, None)
        return existed

    def exists(self, key: str) -> bool:
        self._purge(key)
        return key in self._store


@pytest.fixture
def redis_client() -> FakeRedisClient:
    return FakeRedisClient()


def test_feed_cache_miss_then_hit(redis_client: FakeRedisClient) -> None:
    cache = FeedCache(client=redis_client, ttl_seconds=60)
    query = {"category": "tech", "limit": 3}
    payload = {"items": [{"title": "Headline"}]}

    first = cache.get("user-a", query)
    assert first.outcome == CacheOutcome.MISS
    assert first.payload is None

    assert cache.set("user-a", query, payload) is True

    second = cache.get("user-a", query)
    assert second.outcome == CacheOutcome.HIT
    assert second.payload == payload


def test_feed_cache_miss_after_ttl_expires(redis_client: FakeRedisClient) -> None:
    cache = FeedCache(client=redis_client, ttl_seconds=1)
    query = {"lang": "en"}
    payload = {"items": []}

    cache.set("user-b", query, payload)
    assert cache.get("user-b", query).outcome == CacheOutcome.HIT

    time.sleep(1.1)
    assert cache.get("user-b", query).outcome == CacheOutcome.MISS


def test_feed_cache_bypass_when_redis_unavailable() -> None:
    cache = FeedCache(client=FakeRedisClient(available=False), ttl_seconds=60)
    result = cache.get("user-c", {"q": "x"})
    assert result.outcome == CacheOutcome.BYPASS
    assert cache.set("user-c", {"q": "x"}, {"items": []}) is False


def test_scrape_guard_lock_and_cooldown(redis_client: FakeRedisClient) -> None:
    guard = ScrapeGuard(client=redis_client)

    assert guard.try_acquire_lock("source-1", ttl_seconds=30) is True
    assert guard.try_acquire_lock("source-1", ttl_seconds=30) is False

    assert guard.release_lock("source-1") is True
    assert guard.try_acquire_lock("source-1", ttl_seconds=30) is True

    assert guard.set_cooldown("source-1", ttl_seconds=30) is True
    assert guard.is_on_cooldown("source-1") is True


def test_scrape_guard_best_effort_when_redis_unavailable() -> None:
    guard = ScrapeGuard(client=FakeRedisClient(available=False))
    assert guard.try_acquire_lock("source-2") is True
    assert guard.is_on_cooldown("source-2") is False
