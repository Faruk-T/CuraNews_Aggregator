# Dynamic scraping with Playwright (Day 6 / Issue #6)

JavaScript-rendered and infinite-scroll pages are handled by the `curanews.browser`
package. Social networks (X/Twitter, etc.) may block bots; this project proves the
pattern with an offline HTML fixture first (ADR-003).

## Components

| Module | Role |
|--------|------|
| `browser/playwright_fetcher.py` | Async browser/page lifecycle |
| `browser/scroll.py` | Scroll-until-stable / scroll-until-count |
| `browser/dynamic_listing.py` | Scroll + BeautifulSoup parse into `ListingEntry` |

## Run demo

```powershell
poetry run playwright install chromium
poetry run python scripts/run_playwright_scrape.py
```

Expect `scroll_final > scroll_initial` and at least 4 parsed entries written to
`data/local/playwright_news.jsonl`.

## Fixture

`tests/fixtures/dynamic_news_scroll.html` starts with 2 cards and appends more on scroll.
