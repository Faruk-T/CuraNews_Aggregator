"""Concurrent Playwright tab management (Issue #9).

One shared browser, many pages, concurrency capped by a semaphore
(``SCRAPE_CONCURRENCY``, default 2).
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from curanews.config import get_settings

logger = logging.getLogger("curanews.browser.concurrent")

PrepareHook = Callable[[Page], Awaitable[Any]]


@dataclass(frozen=True, slots=True)
class PageFetchResult:
    """Outcome of one concurrent page fetch."""

    url: str
    html: str | None
    elapsed_seconds: float
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.html is not None


@dataclass(frozen=True, slots=True)
class ConcurrentFetchSummary:
    """Aggregate timing for a parallel page batch."""

    results: tuple[PageFetchResult, ...]
    wall_seconds: float
    concurrency: int

    @property
    def ok_count(self) -> int:
        return sum(1 for r in self.results if r.ok)

    @property
    def sequential_estimate_seconds(self) -> float:
        return sum(r.elapsed_seconds for r in self.results)


class ConcurrentBrowserSession:
    """Share one Chromium process across semaphore-limited tabs."""

    def __init__(
        self,
        browser: Browser,
        *,
        concurrency: int | None = None,
        headless: bool = True,
    ) -> None:
        settings = get_settings()
        self._browser = browser
        self.concurrency = max(1, concurrency or settings.scrape_concurrency)
        self.headless = headless
        self._semaphore = asyncio.Semaphore(self.concurrency)

    async def open_page(self) -> tuple[BrowserContext, Page]:
        context = await self._browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "CuraNewsBot/0.1 (+https://github.com/Faruk-T/CuraNews_Aggregator)"
            ),
        )
        page = await context.new_page()
        return context, page

    async def fetch_html(
        self,
        url: str,
        *,
        prepare: PrepareHook | None = None,
        wait_until: str = "domcontentloaded",
        timeout_ms: int = 30_000,
    ) -> PageFetchResult:
        """Fetch one URL under the concurrency semaphore."""
        started = time.perf_counter()
        async with self._semaphore:
            context: BrowserContext | None = None
            try:
                context, page = await self.open_page()
                await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
                if prepare is not None:
                    await prepare(page)
                html = await page.content()
                elapsed = time.perf_counter() - started
                logger.info(
                    "page_ok url=%s elapsed=%.3fs concurrency=%s",
                    url,
                    elapsed,
                    self.concurrency,
                )
                return PageFetchResult(url=url, html=html, elapsed_seconds=elapsed)
            except Exception as exc:  # noqa: BLE001
                elapsed = time.perf_counter() - started
                logger.warning(
                    "page_fail url=%s elapsed=%.3fs error=%s",
                    url,
                    elapsed,
                    exc,
                )
                return PageFetchResult(
                    url=url,
                    html=None,
                    elapsed_seconds=elapsed,
                    error=str(exc),
                )
            finally:
                if context is not None:
                    await context.close()

    async def fetch_many(
        self,
        urls: Sequence[str],
        *,
        prepare: PrepareHook | None = None,
        wait_until: str = "domcontentloaded",
        timeout_ms: int = 30_000,
    ) -> ConcurrentFetchSummary:
        """Open many URLs in parallel (bounded by ``concurrency``)."""
        wall_start = time.perf_counter()
        tasks = [
            self.fetch_html(
                url,
                prepare=prepare,
                wait_until=wait_until,
                timeout_ms=timeout_ms,
            )
            for url in urls
        ]
        results = await asyncio.gather(*tasks)
        wall = time.perf_counter() - wall_start
        summary = ConcurrentFetchSummary(
            results=tuple(results),
            wall_seconds=wall,
            concurrency=self.concurrency,
        )
        logger.info(
            "batch_done urls=%s ok=%s wall=%.3fs sequential_estimate=%.3fs concurrency=%s",
            len(urls),
            summary.ok_count,
            summary.wall_seconds,
            summary.sequential_estimate_seconds,
            self.concurrency,
        )
        return summary


@asynccontextmanager
async def concurrent_browser(
    *,
    concurrency: int | None = None,
    headless: bool = True,
    browser_type: str = "chromium",
):
    """Yield a ``ConcurrentBrowserSession`` with guaranteed browser shutdown."""
    async with async_playwright() as playwright:
        launcher = getattr(playwright, browser_type)
        browser = await launcher.launch(headless=headless)
        try:
            yield ConcurrentBrowserSession(
                browser,
                concurrency=concurrency,
                headless=headless,
            )
        finally:
            await browser.close()


async def fetch_urls_concurrent(
    urls: Sequence[str],
    *,
    concurrency: int | None = None,
    headless: bool = True,
    prepare: PrepareHook | None = None,
) -> ConcurrentFetchSummary:
    """Convenience wrapper: launch browser, fetch all URLs, close."""
    async with concurrent_browser(concurrency=concurrency, headless=headless) as session:
        return await session.fetch_many(urls, prepare=prepare)
