# Day 15 evidence (Issue #15 / G15)

Staj defteri ek numaraları (öneri): **Ek-25 … Ek-30**.

## Code block screenshots (IDE)

| Ek | File | Class / focus | Screenshot tip |
|----|------|---------------|----------------|
| **Ek-25** | `src/curanews/privacy/pii.py` | `scrub_pii()` — email/phone/handle | `code-pii-scrub.png` |
| **Ek-26** | `src/curanews/nlp/curation.py` | `CurationEngine` + `score_article` / `rank` | `code-curation-engine.png` |
| **Ek-27** | `src/curanews/db/user_repository.py` | `entity_profile` + `record_read` | `code-user-repository.png` |
| **Ek-28** | `scripts/seed_demo_users.py` | User A/B bias seed | `code-seed-demo-users.png` |

## Terminal (Ek-29 / Ek-30)

**Ek-29** — unit tests:

```powershell
poetry run pytest tests/unit/test_curation_pii.py -q
```

**Ek-30** — live ranking + PII:

```powershell
docker compose up -d postgres
poetry run alembic upgrade head
poetry run python scripts/seed_demo_users.py
poetry run python scripts/verify_curation.py
```

Show JSON with `"ranking_differs": true` and `"pii_ok": true`.

## Staj defteri yazımı

Metinde her iddiayı `bkz. Ek-25` … `bkz. Ek-30` ile bağla (dosya yolu + sınıf adı).
