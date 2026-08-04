"""Dynamic listing fetch: Playwright scroll + BeautifulSoup parse (Issue #6)."""

from __future__ import annotations

from pathlib import Path

from curanews.browser.playwright_fetcher import fetch_html_after
from curanews.browser.scroll import ScrollResult, scroll_until_at_least, scroll_until_stable
from curanews.scrapers.parse_bs4 import ListingEntry, parse_example_listing

DEFAULT_ITEM_SELECTOR = "article.news-card"


async def fetch_dynamic_listing(
    url: str,
    *,
    source: str = "dynamic_demo",
    base_url: str = "https://example.com/",
    item_selector: str = DEFAULT_ITEM_SELECTOR,
    min_items: int | None = None,
    headless: bool = True,
) -> tuple[list[ListingEntry], ScrollResult]:
    """Render a dynamic page, scroll for more cards, parse listing entries."""

    async def _prepare(page) -> ScrollResult:  # noqa: ANN001
        if min_items is not None:
            return await scroll_until_at_least(
                page,
                item_selector=item_selector,
                min_items=min_items,
            )
        return await scroll_until_stable(page, item_selector=item_selector)

    scroll_holder: dict[str, ScrollResult] = {}

    async def prepare(page) -> None:  # noqa: ANN001
        scroll_holder["result"] = await _prepare(page)

    html = await fetch_html_after(url, prepare=prepare, headless=headless)
    entries = parse_example_listing(html, base_url=base_url, source=source)
    result = scroll_holder.get(
        "result",
        ScrollResult(rounds=0, final_count=len(entries), initial_count=len(entries)),
    )
    return entries, result


def fixture_file_url(path: Path | None = None) -> str:
    """Return a ``file://`` URL for the Day 6 infinite-scroll fixture."""
    fixture = path or (
        Path(__file__).resolve().parents[3]
        / "tests"
        / "fixtures"
        / "dynamic_news_scroll.html"
    )
    candidates = [
        fixture,
        Path.cwd() / "tests" / "fixtures" / "dynamic_news_scroll.html",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve().as_uri()
    raise FileNotFoundError(f"Dynamic fixture missing: {fixture}")


# silence unused import warning for re-export convenience
__all__ = [
    "DEFAULT_ITEM_SELECTOR",
    "fetch_dynamic_listing",
    "fixture_file_url",
    "ListingEntry",
    "ScrollResult",
]
