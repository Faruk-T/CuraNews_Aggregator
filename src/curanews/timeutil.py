"""Timestamp sanity rules shared by ingestion, ranking and rendering."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

ISTANBUL_OFFSET = timedelta(hours=3)
FUTURE_TOLERANCE = timedelta(minutes=10)


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def correct_future_timestamp(
    value: datetime | None, *, now: datetime | None = None
) -> datetime | None:
    """Fix publisher clocks that label Istanbul local time as GMT.

    Some Turkish feeds (e.g. CNN Türk) emit ``15:22 GMT`` for 15:22 local time, which
    lands three hours in the future. Shift such stamps back by +03:00; anything still
    in the future is clamped to ``now`` so it cannot pin itself to the top of the feed.
    """
    if value is None:
        return None
    current = as_utc(now or datetime.now(UTC))
    stamp = as_utc(value)
    if stamp <= current + FUTURE_TOLERANCE:
        return stamp
    shifted = stamp - ISTANBUL_OFFSET
    if shifted <= current + FUTURE_TOLERANCE:
        return shifted
    return current
