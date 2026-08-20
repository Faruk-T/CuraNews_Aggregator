"""In-memory Redis stand-in used by unit and integration tests."""

from __future__ import annotations

import time


class FakeRedisClient:
    """Minimal Redis client surface used by FeedCache / ScrapeGuard."""

    def __init__(self, *, available: bool = True) -> None:
        self._available = available
        self._store: dict[str, str] = {}
        self._expiry: dict[str, float] = {}

    @property
    def available(self) -> bool:
        return self._available

    def set_available(self, value: bool) -> None:
        self._available = value

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

    def delete_by_prefix(self, prefix: str) -> int:
        keys = [k for k in list(self._store) if k.startswith(prefix)]
        for key in keys:
            self.delete(key)
        return len(keys)

    def exists(self, key: str) -> bool:
        self._purge(key)
        return key in self._store
