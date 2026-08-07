"""Async Playwright browser lifecycle helpers (Issue #6)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from curanews.scrapers.policy import assert_url_allowed, user_agent


@asynccontextmanager
async def launch_browser(
    *,
    headless: bool = True,
    browser_type: str = "chromium",
) -> AsyncIterator[Browser]:
    """Launch a Playwright browser and guarantee clean shutdown."""
    async with async_playwright() as playwright:
        launcher = getattr(playwright, browser_type)
        browser = await launcher.launch(headless=headless)
        try:
            yield browser
        finally:
            await browser.close()


@asynccontextmanager
async def new_page(
    *,
    headless: bool = True,
    viewport: dict[str, int] | None = None,
) -> AsyncIterator[Page]:
    """Yield a single page with context/browser cleanup."""
    async with launch_browser(headless=headless) as browser:
        context: BrowserContext = await browser.new_context(
            viewport=viewport or {"width": 1280, "height": 720},
            user_agent=user_agent(),
        )
        page = await context.new_page()
        try:
            yield page
        finally:
            await context.close()


async def fetch_rendered_html(
    url: str,
    *,
    wait_until: str = "domcontentloaded",
    timeout_ms: int = 30_000,
    headless: bool = True,
) -> str:
    """Open ``url`` in Chromium and return the fully rendered HTML."""
    assert_url_allowed(url)
    async with new_page(headless=headless) as page:
        await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
        return await page.content()


async def fetch_html_after(
    url: str,
    *,
    prepare: Any,
    wait_until: str = "domcontentloaded",
    timeout_ms: int = 30_000,
    headless: bool = True,
) -> str:
    """Open ``url``, run an async ``prepare(page)`` hook, then return HTML."""
    assert_url_allowed(url)
    async with new_page(headless=headless) as page:
        await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
        await prepare(page)
        return await page.content()
