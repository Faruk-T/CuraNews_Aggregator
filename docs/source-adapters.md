# Source adapters (Issue #8 / G8)

CuraNews ingests news through a single **`SourceAdapter`** contract. Static HTML (Scrapy/BS4 path), Playwright dynamic listings, and GNews-style JSON APIs all return **`RawArticleDraft`** rows; **`ingest_from_adapter()`** promotes them to **`NewsArticle`** with the same validation rules as the Scrapy pipeline.

## Contract

| Member | Meaning |
|--------|---------|
| `source_id` | Stable source key |
| `kind` | `static`, `dynamic`, or `api` |
| `fetch(limit=50)` | Synchronous fetch of draft rows |

## Built-in adapters

| Registry name | Class | Data path |
|---------------|-------|-----------|
| `static`, `example_news` | `StaticFixtureAdapter` | `tests/fixtures/example_news_listing.html` |
| `dynamic` | `DynamicFixtureAdapter` | Playwright + `dynamic_news_scroll.html` |
| `api`, `gnews` | `NewsApiAdapter` | Live HTTP or `tests/fixtures/gnews_sample.json` |

List names:

```powershell
poetry run python scripts/fetch_sources.py --list
```

## Shared consumer

```python
from curanews.scrapers.adapters import StaticFixtureAdapter, ingest_from_adapter

articles = ingest_from_adapter(StaticFixtureAdapter(), limit=10)
```

The same function works for static, dynamic, and API adapters — G8 acceptance criterion.

## CLI demo

Offline API (no key):

```powershell
poetry run python scripts/fetch_sources.py --adapter api --promote
poetry run python scripts/fetch_sources.py --adapter static --limit 3 --promote
```

Dynamic (requires Chromium):

```powershell
poetry run playwright install chromium
poetry run python scripts/fetch_sources.py --adapter dynamic --promote --output data/local/dynamic_adapter.jsonl
```

Live API: set `NEWS_API_KEY` in `.env`. HTTP uses Day 7 `call_with_backoff`.

## Related

- [`scraping.md`](./scraping.md)
- [`playwright-scraping.md`](./playwright-scraping.md)
- [`resilience.md`](./resilience.md)
