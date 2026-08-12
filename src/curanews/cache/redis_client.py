"""Redis client wrapper with graceful degradation (Issue #12 / G12)."""

from __future__ import annotations

import logging
from functools import lru_cache

import redis
from redis.exceptions import RedisError

from curanews.config import get_settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Thin Redis wrapper that degrades when the server is unreachable."""

    def __init__(self, url: str, *, socket_connect_timeout: float = 0.5) -> None:
        self._url = url
        self._connect_timeout = socket_connect_timeout
        self._client: redis.Redis | None = None
        self._available = False
        self._connect()

    def _connect(self) -> None:
        try:
            client = redis.from_url(
                self._url,
                decode_responses=True,
                socket_connect_timeout=self._connect_timeout,
                socket_timeout=self._connect_timeout,
            )
            client.ping()
            self._client = client
            self._available = True
            logger.info("redis connected url=%s", self._url)
        except (RedisError, OSError) as exc:
            self._client = None
            self._available = False
            logger.warning("redis unavailable degrade=true error=%s", exc)

    @property
    def available(self) -> bool:
        return self._available and self._client is not None

    def ping(self) -> bool:
        if not self.available:
            return False
        try:
            return bool(self._client.ping())
        except RedisError as exc:
            logger.warning("redis ping failed error=%s", exc)
            self._available = False
            return False

    def get(self, key: str) -> str | None:
        if not self.available:
            return None
        try:
            return self._client.get(key)
        except RedisError as exc:
            logger.warning("redis get failed key=%s error=%s", key, exc)
            return None

    def setex(self, key: str, ttl_seconds: int, value: str) -> bool:
        if not self.available:
            return False
        try:
            return bool(self._client.setex(key, ttl_seconds, value))
        except RedisError as exc:
            logger.warning("redis setex failed key=%s error=%s", key, exc)
            return False

    def set(
        self,
        key: str,
        value: str,
        *,
        nx: bool = False,
        ex: int | None = None,
    ) -> bool:
        if not self.available:
            return False
        try:
            return bool(self._client.set(key, value, nx=nx, ex=ex))
        except RedisError as exc:
            logger.warning("redis set failed key=%s error=%s", key, exc)
            return False

    def delete(self, key: str) -> bool:
        if not self.available:
            return False
        try:
            return bool(self._client.delete(key))
        except RedisError as exc:
            logger.warning("redis delete failed key=%s error=%s", key, exc)
            return False

    def exists(self, key: str) -> bool:
        if not self.available:
            return False
        try:
            return bool(self._client.exists(key))
        except RedisError as exc:
            logger.warning("redis exists failed key=%s error=%s", key, exc)
            return False

    def delete_by_prefix(self, prefix: str) -> int:
        if not self.available:
            return 0
        try:
            removed = 0
            for key in self._client.scan_iter(match=f"{prefix}*"):
                removed += int(self._client.delete(key))
            return removed
        except RedisError as exc:
            logger.warning("redis delete_by_prefix failed prefix=%s error=%s", prefix, exc)
            return 0


@lru_cache(maxsize=1)
def get_redis_client() -> RedisClient:
    settings = get_settings()
    return RedisClient(settings.redis_url)
