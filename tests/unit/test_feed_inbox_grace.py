"""Main-feed grace window for marked-read articles."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from curanews.api.feed_service import still_on_main_feed


def test_unread_stays_on_main_feed() -> None:
    now = datetime(2026, 8, 20, 16, 0, tzinfo=UTC)
    assert still_on_main_feed(None, now=now, grace_seconds=1200) is True


def test_recent_read_stays_on_main_feed() -> None:
    now = datetime(2026, 8, 20, 16, 0, tzinfo=UTC)
    read_at = now - timedelta(minutes=19)
    assert still_on_main_feed(read_at, now=now, grace_seconds=1200) is True


def test_stale_read_leaves_main_feed() -> None:
    now = datetime(2026, 8, 20, 16, 0, tzinfo=UTC)
    read_at = now - timedelta(minutes=21)
    assert still_on_main_feed(read_at, now=now, grace_seconds=1200) is False


def test_grace_boundary_is_inclusive() -> None:
    now = datetime(2026, 8, 20, 16, 0, tzinfo=UTC)
    read_at = now - timedelta(seconds=1200)
    assert still_on_main_feed(read_at, now=now, grace_seconds=1200) is True
