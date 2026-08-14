# Curation + PII (Issue #15 / G15)

Personalized feed scoring (IMPLEMENTATION_PLAN §7.5) and PII scrubbing before display/persist.

## Score formula

\[
score(a,u) = w_t \cdot freshness + w_i \cdot interest + w_d \cdot diversity - w_p \cdot penalty
\]

Defaults: \(w_t=0.30\), \(w_i=0.45\), \(w_d=0.15\), \(w_p=0.10\).

| Term | Meaning |
|------|---------|
| freshness | \(e^{-\lambda \Delta t}\) (hours) |
| interest | Jaccard(user entity profile, article entities) |
| diversity | Penalize repeated `source_id` in recent picks |
| penalty | Empty title / short body / zero entities |

## Run locally

```powershell
docker compose up -d postgres
poetry run alembic upgrade head
poetry run python scripts/seed_sources.py
poetry run python scripts/seed_demo_users.py
poetry run pytest tests/unit/test_curation_pii.py -q
poetry run python scripts/verify_curation.py
```

Expected: `ranking_differs: true`, User A top leans economy/AI, User B sports/climate; PII fixture masked.

## Modules

| Module | Role |
|--------|------|
| `privacy/pii.py` | email / phone / @handle scrub |
| `nlp/curation.py` | `CurationEngine.rank()` |
| `db/user_repository.py` | users, `user_reads`, entity profile |
| `scripts/seed_demo_users.py` | demo-user-a / demo-user-b + biased reads |

## Related

- [`spacy-nlp.md`](./spacy-nlp.md)
- [`ingestion-pipeline.md`](./ingestion-pipeline.md)
