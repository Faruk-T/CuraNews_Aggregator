# Architecture

High-level design for CuraNews Aggregator. Details live in [`IMPLEMENTATION_PLAN.md`](../IMPLEMENTATION_PLAN.md).

## Layers

| Layer | Package | Responsibility |
|-------|---------|----------------|
| Acquisition | `scrapers`, `browser` | Static (Scrapy/BS4) and dynamic (Playwright) fetch |
| Resilience | `resilience` | Backoff, rate limits, polite crawling |
| Privacy | `privacy` | PII mask / pseudonymization |
| Ingestion | `ingestion` | Normalize, dedupe, persist |
| Persistence | `db` | PostgreSQL source of truth |
| Cache | `cache` | Redis feed/scrape locks |
| Intelligence | `nlp` | spaCy entities + curation scores |
| API | `api` | FastAPI REST surface |
| UI | `web/` | Frontend (Phase 4) |

## Data flow (target)

```text
Sources → Adapter.fetch → Privacy.scrub → Normalize/Hash
       → Dedupe/Upsert (Postgres) → NLP tags → Cache invalidate
       → GET /feed → CurationEngine.score → Redis cache → Client
```

Filled in as Issues #3–#20 land.
