"""Tests for exponential backoff policy (Issue #7)."""

import random

from curanews.resilience import BackoffPolicy, should_retry_status


def test_should_retry_status_transient_only():
    assert should_retry_status(429) is True
    assert should_retry_status(503) is True
    assert should_retry_status(404) is False
    assert should_retry_status(400) is False


def test_backoff_delays_increase_with_attempt():
    policy = BackoffPolicy(base_seconds=0.5, cap_seconds=60, max_retries=5, jitter_ratio=0.0)
    rng = random.Random(0)
    delays = policy.iter_delays(rng=rng)
    assert delays == [0.5, 1.0, 2.0, 4.0, 8.0]


def test_backoff_respects_cap():
    policy = BackoffPolicy(base_seconds=10, cap_seconds=15, max_retries=5, jitter_ratio=0.0)
    assert policy.delay_for_attempt(0) == 10
    assert policy.delay_for_attempt(1) == 15
    assert policy.delay_for_attempt(3) == 15
