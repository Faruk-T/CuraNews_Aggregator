"""Playwright integration tests for infinite-scroll fixture (Issue #6)."""

from __future__ import annotations

import pytest

from curanews.browser import fetch_dynamic_listing, fixture_file_url

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
def event_loop_policy():
    # default asyncio policy is fine on Windows for these tests
    return None


async def test_dynamic_fixture_scroll_loads_more_cards():
    pytest.importorskip("playwright")
    url = fixture_file_url()
    entries, scroll = await fetch_dynamic_listing(
        url,
        source="dynamic_demo",
        base_url="https://example.com/",
        min_items=4,
    )
    assert scroll.initial_count >= 1
    assert scroll.final_count > scroll.initial_count
    assert len(entries) >= 4
    assert entries[0].title
    assert entries[0].url.startswith("https://example.com/")
