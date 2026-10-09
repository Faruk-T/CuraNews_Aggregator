# Ingestion pipeline (Issue #13 / G13)

Production path from **SourceAdapter** drafts to **PostgreSQL** articles.

## Flow

```text
Adapter.fetch()
  → clean_raw_draft()
  → promote_draft()          # strict NewsArticle
  → scrub_news_article()     # light PII scrub (expanded in G15)
  → insert_article()         # url_hash dedupe — duplicate → no new row
  → tag_article()            # spaCy NER + TOPIC keywords → article_entities (G14)
  → FeedCache.invalidate_all()   # optional feed:* flush
```

Disable NLP with `--no-nlp` on `run_ingestion.py`.

## Run locally

```powershell
docker compose up -d postgres
poetry run alembic upgrade head
poetry run python scripts/refresh_news.py
poetry run python scripts/run_ingestion.py --adapter rss
```

`refresh_news.py` pulls the full public RSS catalog (AA, TRT, NTV, CNN Türk, Hürriyet, Habertürk, BBC, Guardian, …). Pass `--with-demo` to also seed the local demo users A/B and example stories; production never does. The API scheduler runs the same pass every `INGEST_INTERVAL_MINUTES` (production default 10). A second `run_ingestion.py --adapter rss` should report `"inserted": 0` and `"duplicates" > 0`. `/health` exposes `last_ingest_at` and `last_ingest_inserted` so a silent fetch failure is visible.

## Modules

| Module | Role |
|--------|------|
| `ingestion/pipeline.py` | `IngestionPipeline`, `IngestionStats` |
| `ingestion/normalize.py` | Domain → repository field mapping |
| `privacy/scrub.py` | Email mask + whitespace normalize |
| `scrapers/adapters/consumer.py` | Legacy JSON promote path (unchanged) |

## Acceptance (G13)

- Same `url_hash` on second ingest → **no new row** (`duplicates` counter)
- Unit tests with fixture adapter → green

## Related

- [`postgresql-schema.md`](./postgresql-schema.md)
- [`redis-cache.md`](./redis-cache.md)
- [`source-adapters.md`](./source-adapters.md)
