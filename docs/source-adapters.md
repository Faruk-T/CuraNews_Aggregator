# Source adapters (Issue #8 / G8; RSS catalog G19)

CuraNews ingests news through a single **`SourceAdapter`** contract. Static HTML (Scrapy/BS4 path), Playwright dynamic listings, GNews-style JSON APIs, and **public RSS/Atom feeds** all return **`RawArticleDraft`** rows; **`ingest_from_adapter()`** promotes them to **`NewsArticle`** with the same validation rules as the Scrapy pipeline.

The **production news path is RSS**. Fixture adapters exist for unit tests and demos. GNews is optional and requires `NEWS_API_KEY`.

## Contract

| Member | Meaning |
|--------|---------|
| `source_id` | Stable source key |
| `kind` | `static`, `dynamic`, `api`, or `rss` |
| `fetch(limit=50)` | Synchronous fetch of draft rows |

## Built-in adapters

| Registry name | Class | Data path |
|---------------|-------|-----------|
| `rss` | `RssCatalogAdapter` | BBC, Guardian, NPR, Al Jazeera, AA (live HTTP) |
| `static`, `example_news` | `StaticFixtureAdapter` | `tests/fixtures/example_news_listing.html` |
| `dynamic` | `DynamicFixtureAdapter` | Playwright + `dynamic_news_scroll.html` |
| `api`, `gnews` | `NewsApiAdapter` | Live HTTP **only if** `NEWS_API_KEY` is set; else `gnews_sample.json` |

List names:

```powershell
poetry run python scripts/fetch_sources.py --list
```

## Shared consumer

```python
from curanews.scrapers.adapters import RssCatalogAdapter, ingest_from_adapter

articles = ingest_from_adapter(RssCatalogAdapter(), limit=20)
```

The same function works for static, dynamic, API, and RSS adapters.

## CLI — real headlines

```powershell
poetry run python scripts/run_ingestion.py --adapter rss --limit 40
# or
poetry run python scripts/refresh_news.py
```

Offline fixtures (no network):

```powershell
poetry run python scripts/fetch_sources.py --adapter api --promote
poetry run python scripts/fetch_sources.py --adapter static --limit 3 --promote
```

Dynamic (requires Chromium):

```powershell
poetry run playwright install chromium
poetry run python scripts/fetch_sources.py --adapter dynamic --promote --output data/local/dynamic_adapter.jsonl
```

Optional GNews JSON API: set `NEWS_API_KEY` in `.env`. HTTP uses Day 7 `call_with_backoff`. Without a key this adapter **does not** call the internet; it loads two fixture articles.

## Field mapping (full drafts)

**RSS/Atom:** `title`, `link`/`guid`, `description`/`content:encoded`/`summary`, `pubDate`/`published`, `category`, `dc:creator`/`author`.

**GNews JSON:** `title`, `url`, `content`, `description`, `publishedAt`, `category`, `author`, `lang`, `image`, `source.name`, `source.url`.

**Static HTML cards:** `data-category`, `data-published`, `data-author`, `data-language`, `data-image`, `.news-summary`, `.news-body`.

Optional fields flow into `RawArticleDraft` and survive `promote_draft()` → `NewsArticle` (`summary`, `author`, `language`, `metadata`).

## Related

- [`sources.md`](./sources.md)
- [`scraping.md`](./scraping.md)
- [`playwright-scraping.md`](./playwright-scraping.md)
- [`resilience.md`](./resilience.md)
