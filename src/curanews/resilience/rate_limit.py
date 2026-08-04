"""Simple in-memory rate limit / cooldown helpers (Issue #7)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class CooldownRegistry:
    """Track per-source cooldown deadlines (seconds since epoch)."""

    _deadlines: dict[str, float] = field(default_factory=dict)

    def set_cooldown(self, source_key: str, seconds: float, *, now: float | None = None) -> None:
        current = time.time() if now is None else now
        self._deadlines[source_key] = current + max(0.0, seconds)

    def remaining(self, source_key: str, *, now: float | None = None) -> float:
        current = time.time() if now is None else now
        deadline = self._deadlines.get(source_key, 0.0)
        return max(0.0, deadline - current)

    def is_cooling(self, source_key: str, *, now: float | None = None) -> bool:
        return self.remaining(source_key, now=now) > 0
