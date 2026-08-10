# PostgreSQL (Issue #11)

Run Postgres locally:

```powershell
docker compose up -d postgres
```

Ensure `.env` matches (host port **5433** — see `docker-compose.yml`; avoids Windows local PostgreSQL on 5432):

```env
DATABASE_URL=postgresql+psycopg://curanews:curanews@localhost:5433/curanews
```

Apply schema:

```powershell
poetry run alembic upgrade head
poetry run python scripts/seed_sources.py
poetry run python scripts/pg_smoke_crud.py
```

## Schema (§7.2)

| Table | Purpose |
|-------|---------|
| `users` | Reader identity (`external_key`) |
| `sources` | Crawl/API source registry |
| `articles` | Normalized news rows (`url_hash` unique) |
| `entities` / `article_entities` | NLP links (G14) |
| `user_reads` | Read/dwell tracking (G18) |

## ORM layout

| Module | Role |
|--------|------|
| `db/models.py` | SQLAlchemy 2 mapped classes |
| `db/repository.py` | Insert/select smoke API |
| `db/session.py` | Engine + session factory |
| `alembic/versions/001_initial_schema.py` | Initial migration |

SQLite remains for Scrapy demos (`SqliteArticleStore`); PostgreSQL is the Faz 3 source of truth.

## Related

- [`pipeline.md`](./pipeline.md)
- [`data-model.md`](./data-model.md)
