# CuraNews Aggregator

Social-media and web-backed dynamic news aggregator (internship project, 20 days).

> Collect → normalize → enrich (NLP) → curate → serve via API/UI

## Status

| Phase | Focus | Progress |
|-------|--------|----------|
| Phase 1 | Setup, Scrapy skeleton, early pipeline | In progress (Day 1) |
| Phase 2 | Playwright, backoff, async fetch | Not started |
| Phase 3 | PostgreSQL/Redis, spaCy, curation, PII | Not started |
| Phase 4 | REST API, frontend, tests, release | Not started |

Tracking: [GitHub Issues](https://github.com/Faruk-T/CuraNews_Aggregator/issues) · Plan: [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md)

## Day 1 — Project skeleton

This repository currently provides the **folder layout**, package entrypoint, and documentation stubs required by
[Issue #1](https://github.com/Faruk-T/CuraNews_Aggregator/issues/1).

```bash
# from repo root (after Day 2 dependency pinning)
python -m curanews
```

Expected output today (no third-party deps required):

```text
CuraNews Aggregator — skeleton OK (day 1)
package: curanews
```

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
