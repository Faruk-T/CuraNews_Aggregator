"""Playwright-based dynamic fetchers — Issue #6+ / #9."""

from curanews.browser.concurrent import (
    ConcurrentBrowserSession,
    ConcurrentFetchSummary,
    PageFetchResult,
    concurrent_browser,
    fetch_urls_concurrent,
)
from curanews.browser.dynamic_listing import fetch_dynamic_listing, fixture_file_url
from curanews.browser.playwright_fetcher import fetch_rendered_html, launch_browser, new_page
from curanews.browser.scroll import ScrollResult, scroll_until_at_least, scroll_until_stable

__all__ = [
    "ConcurrentBrowserSession",
    "ConcurrentFetchSummary",
    "PageFetchResult",
    "ScrollResult",
    "concurrent_browser",
    "fetch_dynamic_listing",
    "fetch_rendered_html",
    "fetch_urls_concurrent",
    "fixture_file_url",
    "launch_browser",
    "new_page",
    "scroll_until_at_least",
    "scroll_until_stable",
]
