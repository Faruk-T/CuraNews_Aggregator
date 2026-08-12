# Day 13 evidence (Issue #13 / G13)

## Code block screenshots (IDE)

| File | Screenshot | Highlight |
|------|------------|-----------|
| `src/curanews/ingestion/pipeline.py` | `code-ingestion-pipeline.png` | `ingest_adapter()` loop + stats |
| `src/curanews/ingestion/normalize.py` | `code-article-normalize.png` | `article_to_persistence_kwargs()` |
| `src/curanews/privacy/scrub.py` | `code-privacy-scrub.png` | email redaction before persist |
| `src/curanews/db/repository.py` | `code-url-hash-dedupe.png` | `insert_article` duplicate guard |

## Terminal (Ek-23 önerisi)

```powershell
docker compose up -d postgres
poetry run alembic upgrade head
poetry run python scripts/seed_sources.py
poetry run pytest tests/unit/test_ingestion_pipeline.py -q
poetry run python scripts/run_ingestion.py --adapter static
poetry run python scripts/run_ingestion.py --adapter static
```

Show first run `inserted > 0`, second run `duplicates > 0` and `inserted: 0`.

## Staj defteri

Explain adapter → clean → scrub → dedupe → Postgres chain and why duplicate URLs do not create a second row.
