# Data pipeline (Day 5 / Issue #5)

Scraped `NewsItem` rows pass through Scrapy pipelines before they become durable.

## Pipeline order

| Priority | Pipeline | Role |
|----------|----------|------|
| 100 | `NewsItemCleaningPipeline` | Trim/collapse whitespace, normalize category |
| 200 | `NewsItemValidationPipeline` | Drop incomplete items (`DropItem`) |
| 300 | `NewsItemDeduplicationPipeline` | Skip known `url_hash` (DB + in-crawl set) |
| 400 | `SqlitePersistPipeline` | Insert into SQLite |

```text
Spider → clean → validate → dedupe → SQLite
                              synchro with JSONL feed export
```

## SQLite

- Default path: `data/local/curanews.sqlite3` (gitignored)
- Unique key: `url_hash` = SHA-256 of canonical URL
- Override: `SQLITE_PATH` env / `--sqlite` on `scripts/run_scrape.py`

## Commands

```powershell
poetry run python scripts/run_scrape.py
poetry run python scripts/run_scrape.py   # second run should not grow unique rows
poetry run python scripts/inspect_db.py
```

## Note on Redis / PostgreSQL

Issue #5 stores and dedupes in **SQLite** for a fast Phase 1 vertical.
PostgreSQL + Redis arrive in Phase 3 (Issues #11 / #12) without changing the pipeline contract.
