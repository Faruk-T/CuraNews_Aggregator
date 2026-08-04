"""Infinite-scroll helpers for dynamic pages (Issue #6)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from playwright.async_api import Page


@dataclass(frozen=True, slots=True)
class ScrollResult:
    """Outcome of a scroll session."""

    rounds: int
    final_count: int
    initial_count: int


async def scroll_until_stable(
    page: Page,
    *,
    item_selector: str,
    max_rounds: int = 12,
    settle_ms: int = 400,
    stable_rounds_needed: int = 2,
) -> ScrollResult:
    """Scroll to bottom until item count stops growing or ``max_rounds`` hits.

    Designed for infinite-scroll feeds where new cards appear after scroll.
    """
    initial = await page.locator(item_selector).count()
    previous = initial
    stable = 0
    rounds = 0

    for rounds in range(1, max_rounds + 1):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(settle_ms)
        current = await page.locator(item_selector).count()
        if current <= previous:
            stable += 1
            if stable >= stable_rounds_needed:
                return ScrollResult(
                    rounds=rounds,
                    final_count=current,
                    initial_count=initial,
                )
        else:
            stable = 0
            previous = current

    final_count = await page.locator(item_selector).count()
    return ScrollResult(rounds=rounds, final_count=final_count, initial_count=initial)


async def scroll_until_at_least(
    page: Page,
    *,
    item_selector: str,
    min_items: int,
    max_rounds: int = 20,
    settle_ms: int = 400,
) -> ScrollResult:
    """Scroll until at least ``min_items`` matching nodes exist (or rounds end)."""
    initial = await page.locator(item_selector).count()
    current = initial
    rounds = 0

    for rounds in range(1, max_rounds + 1):
        current = await page.locator(item_selector).count()
        if current >= min_items:
            return ScrollResult(
                rounds=rounds - 1 if rounds > 1 else 0,
                final_count=current,
                initial_count=initial,
            )
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(settle_ms)
        await asyncio.sleep(0)  # yield to event loop

    current = await page.locator(item_selector).count()
    return ScrollResult(rounds=rounds, final_count=current, initial_count=initial)
