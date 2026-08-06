"""Tests for Issue #9 concurrent Playwright tab session (no real network)."""

from __future__ import annotations

import pytest

from curanews.browser.concurrent import fetch_urls_concurrent
from curanews.browser.dynamic_listing import fixture_file_url
from curanews.scrapers.adapters._paths import fixture_path

pytest.importorskip("playwright")


def _fixture_uris() -> list[str]:
    static = fixture_path("tests", "fixtures", "example_news_listing.html")
    assert static.is_file()
    return [static.resolve().as_uri(), fixture_file_url()]


@pytest.mark.asyncio
async def test_fetch_urls_concurrent_opens_local_fixtures() -> None:
    urls = _fixture_uris()
    try:
        summary = await fetch_urls_concurrent(urls, concurrency=2, headless=True)
    except Exception as exc:  # noqa: BLE001
        if "Executable doesn't exist" in str(exc) or "playwright install" in str(exc).lower():
            pytest.skip("Chromium not installed for Playwright")
        raise

    assert summary.ok_count == 2
    assert summary.concurrency == 2
    assert all(r.html and "news" in r.html.lower() for r in summary.results if r.ok)
    # Shared browser + parallel tabs: wall clock under sum of individual pages.
    assert summary.wall_seconds <= summary.sequential_estimate_seconds + 0.05
