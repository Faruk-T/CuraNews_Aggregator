# CuraNews Aggregator

Social-media and web-backed dynamic news aggregator (internship project, 20 days).

> Collect → normalize → enrich (NLP) → curate → serve via API/UI

## Status

| Phase | Focus | Progress |
|-------|--------|----------|
| Phase 1 | Setup, Scrapy skeleton, early pipeline | Complete (Days 1–5) |
| Phase 2 | Playwright, backoff, adapters, async parallel | In progress (Day 9) |
| Phase 3 | PostgreSQL/Redis, spaCy, curation, PII | Not started |
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

## Issues completed

- [x] [#1](https://github.com/Faruk-T/CuraNews_Aggregator/issues/1) Project skeleton
- [x] [#2](https://github.com/Faruk-T/CuraNews_Aggregator/issues/2) Dependency pinning
- [x] [#3](https://github.com/Faruk-T/CuraNews_Aggregator/issues/3) News item / data models
- [x] [#4](https://github.com/Faruk-T/CuraNews_Aggregator/issues/4) Scrapy base spider
- [x] [#5](https://github.com/Faruk-T/CuraNews_Aggregator/issues/5) SQLite pipeline + dedupe
- [x] [#6](https://github.com/Faruk-T/CuraNews_Aggregator/issues/6) Playwright dynamic scrape
- [x] [#7](https://github.com/Faruk-T/CuraNews_Aggregator/issues/7) Exponential backoff
- [x] [#8](https://github.com/Faruk-T/CuraNews_Aggregator/issues/8) SourceAdapter + news API
- [ ] [#9](https://github.com/Faruk-T/CuraNews_Aggregator/issues/9) Async parallel fetch (Day 9 branch)

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

## License

Internship / coursework use unless otherwise stated.
