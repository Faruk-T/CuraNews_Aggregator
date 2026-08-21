# Architecture (Issue #20 / G20)

CuraNews Aggregator: collect → normalize → enrich → curate → serve.

## Topology (Compose)

```text
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Browser    │────▶│  api         │────▶│  postgres   │
│  /ui /docs  │     │  FastAPI     │     │  articles   │
└─────────────┘     │  + static UI │────▶│  users/reads│
                    └──────┬───────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  redis       │
                    │  feed cache  │
                    └──────────────┘
```

`docker compose up --build` starts **postgres**, **redis**, and **api**.  
The API image runs migrations, optionally bootstraps RSS + demo users (`CURANEWS_BOOTSTRAP=1`), then serves `uvicorn curanews.api.app:app`.

## Layers

| Layer | Package | Responsibility |
|-------|---------|----------------|
| Acquisition | `scrapers`, `browser` | RSS catalog (live), Scrapy/BS4 fixtures, Playwright demo |
| Resilience | `resilience` | Exponential backoff, rate limits, allowlist |
| Privacy | `privacy` | PII scrub before persist/serve |
| Ingestion | `ingestion` | Normalize → dedupe → Postgres upsert |
| Persistence | `db` | SQLAlchemy models + Alembic |
| Cache | `cache` | Redis feed HIT/MISS + scrape locks |
| Intelligence | `nlp` | spaCy entities + `CurationEngine` ranking |
| API | `api` | FastAPI routers (`/health`, `/articles`, `/feed`, `/reads`, `/topics`) |
| UI | `web/` | Editorial desk at `/ui/` |

## Data flow

```text
Publisher RSS (allowlisted)
  → RssCatalogAdapter.fetch (round-robin)
  → Privacy.scrub → Normalize/Hash
  → Dedupe/Upsert (Postgres) → NLP entity links
  → FeedCache.invalidate
  → GET /feed → CurationEngine.rank
  → Redis SETEX (TTL) → Client / UI
```

Read marks stay on the main feed for `READ_INBOX_GRACE_SECONDS` (default 20 min), then move to `read_items` (Okunanlar) without deleting `user_reads`.

## Key modules

| Path | Role |
|------|------|
| `scrapers/adapters/rss_catalog.py` | Official RSS/Atom feed list |
| `ingestion/pipeline.py` | Ingest adapter → DB |
| `nlp/curation.py` | Score + rank per user profile |
| `api/feed_service.py` | Cache + grace window + feed payload |
| `cache/feed_cache.py` | Redis get/set/invalidate |
| `web/app.js` | Personas, filters, Okundu / Okunanlar |

## Related docs

- [`sources.md`](./sources.md) — allowlist + catalog
- [`testing.md`](./testing.md) — G19 pyramid
- [`demo.md`](./demo.md) — mentor 10-minute script
- [`fastapi-api.md`](./fastapi-api.md) — HTTP contract
