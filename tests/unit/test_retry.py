"""Tests for retry wrapper and cooldown registry."""

from curanews.resilience import (
    BackoffPolicy,
    CooldownRegistry,
    RetryExhaustedError,
    call_with_backoff,
)
import pytest


class FakeHttpError(Exception):
    def __init__(self, status_code: int):
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code


def test_cooldown_registry():
    reg = CooldownRegistry()
    reg.set_cooldown("src", 5, now=100.0)
    assert reg.is_cooling("src", now=102.0) is True
    assert reg.remaining("src", now=102.0) == pytest.approx(3.0)
    assert reg.is_cooling("src", now=106.0) is False


def test_call_with_backoff_eventually_succeeds():
    attempts = {"n": 0}
    slept: list[float] = []

    def operation():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise FakeHttpError(503)
        return "ok"

    result = call_with_backoff(
        operation,
        policy=BackoffPolicy(base_seconds=0.1, max_retries=5, jitter_ratio=0.0),
        sleep=slept.append,
    )
    assert result == "ok"
    assert attempts["n"] == 3
    assert slept == [0.1, 0.2]


def test_call_with_backoff_exhausts_on_persistent_429():
    slept: list[float] = []

    def operation():
        raise FakeHttpError(429)

    with pytest.raises(RetryExhaustedError):
        call_with_backoff(
            operation,
            policy=BackoffPolicy(base_seconds=0.1, max_retries=3, jitter_ratio=0.0),
            sleep=slept.append,
        )
    assert len(slept) == 2  # retries between 3 attempts
