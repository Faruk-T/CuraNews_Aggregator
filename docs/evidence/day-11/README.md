# Day 11 evidence (Issue #11 / G11)

## Code block screenshots (IDE)

| File | Screenshot | Highlight |
|------|------------|-----------|
| `src/curanews/db/models.py` | `code-orm-article-model.png` | `Article` table + `url_hash` unique |
| `src/curanews/db/repository.py` | `code-article-repository.png` | `insert_article` + duplicate guard |
| `alembic/versions/001_initial_schema.py` | `code-alembic-upgrade.png` | `upgrade()` create tables |
| `docker-compose.yml` | `code-docker-postgres.png` | Postgres service definition |

## Terminal (Ek-21 önerisi)

Single screenshot combining:

```powershell
docker compose up -d postgres
poetry run alembic upgrade head
poetry run pytest tests/unit/test_db_repository.py -q
poetry run python scripts/seed_sources.py
poetry run python scripts/pg_smoke_crud.py
```

Show `alembic upgrade head` success + smoke JSON with `"status": "inserted"`.
