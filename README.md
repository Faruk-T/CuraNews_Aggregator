# CuraNews Aggregator

Social-media and web-backed dynamic news aggregator (internship project, 20 days).

> Collect → normalize → enrich (NLP) → curate → serve via API/UI

## Status

| Phase | Focus | Progress |
|-------|--------|----------|
| Phase 1 | Setup, Scrapy skeleton, early pipeline | Complete (Days 1–5) |
| Phase 2 | Playwright, backoff, adapters, parallel, policy | Complete (Days 6–10) |
| Phase 3 | PostgreSQL/Redis, spaCy, curation, PII | In progress (Day 14) |
| Phase 4 | REST API, frontend, tests, release | Not started |

Tracking: [GitHub Issues](https://github.com/Faruk-T/CuraNews_Aggregator/issues) · Plan: [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md)

## Quick start

Requires **Python 3.11–3.13** and [Poetry](https://python-poetry.org/).

```powershell
python -m pip install poetry
poetry install
poetry run playwright install chromium
poetry run python -m curanews
poetry run pytest
poetry run python scripts/run_scrape.py
poetry run python scripts/inspect_db.py
poetry run python scripts/run_playwright_scrape.py
poetry run python scripts/fetch_sources.py --adapter api --promote
poetry run python scripts/run_parallel_fetch.py --adapters static,api
poetry run python scripts/verify_crawl_policy.py
docker compose up -d postgres
poetry run alembic upgrade head
poetry run python scripts/pg_smoke_crud.py
docker compose up -d redis
poetry run python scripts/verify_redis_cache.py --ttl 2
poetry run python scripts/run_ingestion.py --adapter static
poetry run python -m spacy download en_core_web_sm
poetry run python scripts/verify_spacy_nlp.py --require-model
```

Copy `.env.example` → `.env` for local overrides (never commit `.env`).

- Dependency pinning: [`docs/dependency-pinning.md`](./docs/dependency-pinning.md)
- Data model: [`docs/data-model.md`](./docs/data-model.md)
- Scraping: [`docs/scraping.md`](./docs/scraping.md)
- Pipeline / SQLite: [`docs/pipeline.md`](./docs/pipeline.md)
- Playwright: [`docs/playwright-scraping.md`](./docs/playwright-scraping.md)
- Resilience / backoff: [`docs/resilience.md`](./docs/resilience.md)
- Source adapters: [`docs/source-adapters.md`](./docs/source-adapters.md)
- Async parallel fetch: [`docs/async-parallel-fetch.md`](./docs/async-parallel-fetch.md)
- Polite crawling / cleaning: [`docs/polite-crawling.md`](./docs/polite-crawling.md)
- PostgreSQL schema: [`docs/postgresql-schema.md`](./docs/postgresql-schema.md)
- Redis cache: [`docs/redis-cache.md`](./docs/redis-cache.md)
- Ingestion pipeline: [`docs/ingestion-pipeline.md`](./docs/ingestion-pipeline.md)
- spaCy NLP: [`docs/spacy-nlp.md`](./docs/spacy-nlp.md)
- Allowed sources: [`docs/sources.md`](./docs/sources.md)

## Issues completed

- [x] [#1](https://github.com/Faruk-T/CuraNews_Aggregator/issues/1) Project skeleton
- [x] [#2](https://github.com/Faruk-T/CuraNews_Aggregator/issues/2) Dependency pinning
- [x] [#3](https://github.com/Faruk-T/CuraNews_Aggregator/issues/3) News item / data models
- [x] [#4](https://github.com/Faruk-T/CuraNews_Aggregator/issues/4) Scrapy base spider
- [x] [#5](https://github.com/Faruk-T/CuraNews_Aggregator/issues/5) SQLite pipeline + dedupe
- [x] [#6](https://github.com/Faruk-T/CuraNews_Aggregator/issues/6) Playwright dynamic scrape
- [x] [#7](https://github.com/Faruk-T/CuraNews_Aggregator/issues/7) Exponential backoff
- [x] [#8](https://github.com/Faruk-T/CuraNews_Aggregator/issues/8) SourceAdapter + news API
- [x] [#9](https://github.com/Faruk-T/CuraNews_Aggregator/issues/9) Async parallel fetch
- [x] [#10](https://github.com/Faruk-T/CuraNews_Aggregator/issues/10) Cleaning + polite crawl
- [x] [#11](https://github.com/Faruk-T/CuraNews_Aggregator/issues/11) PostgreSQL schema + ORM
- [x] [#12](https://github.com/Faruk-T/CuraNews_Aggregator/issues/12) Redis cache + scrape guard
- [x] [#13](https://github.com/Faruk-T/CuraNews_Aggregator/issues/13) Ingestion pipeline + dedupe
- [ ] [#14](https://github.com/Faruk-T/CuraNews_Aggregator/issues/14) spaCy NLP entities (Day 14 branch)

## Planned layout

```text
src/curanews/          # application package
  scrapers/            # Scrapy / BeautifulSoup adapters
  browser/             # Playwright workers
  resilience/          # backoff, rate limits
  privacy/             # PII pseudonymization
  ingestion/           # normalize → dedupe → persist
  db/                  # ORM / migrations helpers
  cache/               # Redis client
  nlp/                 # spaCy + curation
  api/                 # FastAPI routers
docs/                  # architecture & process docs
tests/                 # unit & integration tests
web/                   # frontend (Phase 4)
scripts/               # scrape/seed helpers
```

## Methodology

Scrumban (Scrum cadence + Kanban WIP/pull) with 4 milestones × ~5 days. See `IMPLEMENTATION_PLAN.md`.

## Ethical crawling (Faz 2)

- Fetch only hosts listed in `SCRAPE_ALLOWLIST_HOSTS` (see [`docs/sources.md`](./docs/sources.md)).
- Use the identifying `CuraNewsBot/0.1` User-Agent; do not impersonate a browser user.
- Keep concurrency at **2** or lower unless mentor approves a change.
- Strip HTML/noise and validate required fields before persisting or serving articles.
- Prefer offline fixtures for demos; live sites require permission and robots/ToS review.

## License

Internship / coursework use unless otherwise stated.
