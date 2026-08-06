# Async parallel fetch (Issue #9)

CuraNews can scrape **multiple sources at once** using Python `asyncio`.
Concurrency is capped by `SCRAPE_CONCURRENCY` (default **2**) so the bot stays polite.

## Two layers

| Layer | Module | What it parallelizes |
|-------|--------|----------------------|
| Browser tabs | `browser/concurrent.py` | Many Playwright **pages** on **one** Chromium process |
| Source adapters | `scrapers/parallel.py` | Many `SourceAdapter.fetch()` calls via `asyncio.to_thread` |

## Why one browser + many pages?

Launching a full Chromium per URL is expensive. Issue #9 asks for concurrent **tab** management: share the browser, open a context/page per URL, close the context when done, and limit in-flight tabs with an `asyncio.Semaphore`.

## CLI demo

```powershell
poetry run python scripts/run_parallel_fetch.py --adapters static,api --concurrency 2
poetry run python scripts/run_parallel_fetch.py --browser-demo
```

The JSON summary prints:

- `wall_seconds` — real elapsed time for the batch
- `sequential_estimate_seconds` — sum of per-task times (if run one-by-one)
- When parallel works, **wall ≪ sequential estimate**

## Programmatic use

```python
from curanews.scrapers.adapters import get_adapter
from curanews.scrapers.parallel import ingest_adapters_parallel_sync

summary = ingest_adapters_parallel_sync(
    [get_adapter("static"), get_adapter("api")],
    limit=10,
    concurrency=2,
)
print(summary.article_count, summary.wall_seconds)
```

## Settings

| Env | Default | Role |
|-----|---------|------|
| `SCRAPE_CONCURRENCY` | `2` | Max parallel workers / tabs |

## Related

- [`source-adapters.md`](./source-adapters.md) — Day 8 adapters
- [`playwright-scraping.md`](./playwright-scraping.md) — Day 6 browser helpers
- [`resilience.md`](./resilience.md) — Day 7 backoff
