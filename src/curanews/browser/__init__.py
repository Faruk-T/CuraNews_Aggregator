"""Playwright-based dynamic fetchers — Issue #6+."""

from curanews.browser.dynamic_listing import fetch_dynamic_listing, fixture_file_url
from curanews.browser.playwright_fetcher import fetch_rendered_html, launch_browser, new_page
from curanews.browser.scroll import ScrollResult, scroll_until_at_least, scroll_until_stable

__all__ = [
    "ScrollResult",
    "fetch_dynamic_listing",
    "fetch_rendered_html",
    "fixture_file_url",
    "launch_browser",
    "new_page",
    "scroll_until_at_least",
    "scroll_until_stable",
]
