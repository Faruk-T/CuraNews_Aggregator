"""Small in-process sliding-window rate limiter for abuse-prone endpoints."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class SlidingWindowLimiter:
    def __init__(self, *, limit: int, window_seconds: float) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, *, now: float | None = None) -> bool:
        """Record one attempt; return False when the key is over its budget."""
        current = time.monotonic() if now is None else now
        with self._lock:
            bucket = self._hits[key]
            while bucket and current - bucket[0] > self.window:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return False
            bucket.append(current)
            if len(self._hits) > 50_000:
                self._hits.clear()
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


def client_ip(request: Request) -> str:
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce(limiter: SlidingWindowLimiter, key: str) -> None:
    if not limiter.hit(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Çok fazla istek gönderdiniz. Lütfen biraz sonra tekrar deneyin.",
        )


login_limiter = SlidingWindowLimiter(limit=10, window_seconds=300)
register_limiter = SlidingWindowLimiter(limit=5, window_seconds=3600)
comment_limiter = SlidingWindowLimiter(limit=5, window_seconds=60)
like_limiter = SlidingWindowLimiter(limit=60, window_seconds=60)


def reset_all() -> None:
    for limiter in (login_limiter, register_limiter, comment_limiter, like_limiter):
        limiter.reset()
