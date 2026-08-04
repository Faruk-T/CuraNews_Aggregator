"""Exponential backoff with full-jitter (Issue #7)."""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BackoffPolicy:
    """Retry delay policy: ``min(cap, base * 2**attempt) + jitter``."""

    base_seconds: float = 0.5
    cap_seconds: float = 60.0
    max_retries: int = 5
    jitter_ratio: float = 0.2

    def delay_for_attempt(self, attempt: int, *, rng: random.Random | None = None) -> float:
        """Return sleep seconds for zero-based ``attempt`` index."""
        if attempt < 0:
            raise ValueError("attempt must be >= 0")
        expo = min(self.cap_seconds, self.base_seconds * (2**attempt))
        jitter_span = expo * self.jitter_ratio
        picker = rng.uniform if rng is not None else random.uniform
        jitter = picker(0.0, jitter_span)
        return expo + jitter

    def iter_delays(self, *, rng: random.Random | None = None) -> list[float]:
        """Materialize delays for attempts ``0 .. max_retries-1`` (for tests/logs)."""
        return [self.delay_for_attempt(i, rng=rng) for i in range(self.max_retries)]


def should_retry_status(status_code: int) -> bool:
    """Return True for transient HTTP statuses worth retrying."""
    return status_code in {408, 429, 500, 502, 503, 504}
