# Polite crawling & data cleaning (Issue #10 / G10)

CuraNews embeds **ethical crawl limits** and **text normalization** before articles are promoted or stored.

## Host allowlist

Outbound HTTP/browser fetches call `assert_url_allowed()` (`src/curanews/scrapers/policy.py`):

- Allowed hosts come from `SCRAPE_ALLOWLIST_HOSTS` (comma-separated).
- `file://` fixture URLs are always permitted (offline demos).
- Unknown hosts raise `HostNotAllowedError` (fail closed).

Demo:

```powershell
poetry run python scripts/verify_crawl_policy.py
```

## User-Agent

Single source: `user_agent()` in `policy.py`, used by Scrapy settings, Playwright, and concurrent browser sessions.

## Concurrency

Default `SCRAPE_CONCURRENCY=2` (also Scrapy `CONCURRENT_REQUESTS=2`). Parallel fetch resolves workers via `assert_concurrency_polite()`.

## Cleaning pipeline (Issue #10)

`clean_news_payload()` / `clean_raw_draft()` (`src/curanews/ingestion/cleaning.py`):

- Collapse whitespace on text fields
- Strip HTML tags from `content` and `summary`
- Normalize `category` to lowercase slug

Adapter ingestion runs `clean_raw_draft()` inside `ingest_from_adapter()` before `promote_draft()`.

Scrapy path: `NewsItemCleaningPipeline` → validate → dedupe → SQLite (unchanged order).

## Source registry

See [`sources.md`](./sources.md) for documented demo sources.

## Related

- [`pipeline.md`](./pipeline.md)
- [`resilience.md`](./resilience.md)
- [`async-parallel-fetch.md`](./async-parallel-fetch.md)
