"""Retry wrapper that applies exponential backoff + cooldown (Issue #7)."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

from curanews.resilience.backoff import BackoffPolicy, should_retry_status
from curanews.resilience.rate_limit import CooldownRegistry

T = TypeVar("T")
logger = logging.getLogger("curanews.resilience")


class RetryExhaustedError(RuntimeError):
    """Raised when all retry attempts fail."""


def call_with_backoff(
    operation: Callable[[], T],
    *,
    policy: BackoffPolicy | None = None,
    source_key: str = "default",
    cooldowns: CooldownRegistry | None = None,
    sleep: Callable[[float], None] = time.sleep,
    classify_exception: Callable[[BaseException], bool] | None = None,
) -> T:
    """Execute ``operation`` with exponential backoff on transient failures.

    ``operation`` should raise an exception with optional ``status_code`` attribute
    (e.g. custom HTTP errors) or a generic exception classified by
    ``classify_exception``.
    """
    policy = policy or BackoffPolicy()
    cooldowns = cooldowns or CooldownRegistry()
    classify = classify_exception or (_default_classify)

    if cooldowns.is_cooling(source_key):
        wait = cooldowns.remaining(source_key)
        logger.info("source=%s cooling remaining=%.3fs", source_key, wait)
        sleep(wait)

    last_error: BaseException | None = None
    for attempt in range(policy.max_retries):
        try:
            return operation()
        except BaseException as exc:  # noqa: BLE001
            last_error = exc
            retryable = classify(exc)
            status = getattr(exc, "status_code", None)
            if status is not None:
                retryable = should_retry_status(int(status))
            if not retryable or attempt >= policy.max_retries - 1:
                break
            delay = policy.delay_for_attempt(attempt)
            logger.warning(
                "retry source=%s attempt=%s delay=%.3fs error=%s",
                source_key,
                attempt,
                delay,
                exc,
            )
            cooldowns.set_cooldown(source_key, delay)
            sleep(delay)

    assert last_error is not None
    raise RetryExhaustedError(
        f"retries exhausted for source={source_key}: {last_error}"
    ) from last_error


def _default_classify(exc: BaseException) -> bool:
    """Retry timeouts / connection-like errors by default."""
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    markers = ("timeout", "temporarily", "connection", "reset", "unavailable")
    return any(marker in name or marker in text for marker in markers)
