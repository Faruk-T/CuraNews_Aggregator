# FastAPI REST skeleton (Issue #16 / G16)

HTTP surface for CuraNews — OpenAPI at `/docs`.

## Run

```powershell
poetry run python scripts/run_api.py
```

Open: http://127.0.0.1:8000/docs · http://127.0.0.1:8000/health

## Endpoints (§7.6)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/health` | app + db/redis probe |
| GET | `/articles` | paginated list (`limit`, `offset`, `source`, `q`) |
| GET | `/articles/{id}` | detail |
| GET | `/feed?user_id=` | curated ranking; body `cache` + header `X-Cache` (`hit`/`miss`/`bypass`) |
| POST | `/reads` | `{user_id, article_id, dwell_ms?}` — invalidates user feed cache (G17) |
| GET | `/topics` | popular entities |

## Modules

| Path | Role |
|------|------|
| `api/app.py` | `create_app()` / `app` |
| `api/schemas.py` | Pydantic response models |
| `api/deps.py` | `get_db` session dependency |
| `api/routers/*.py` | route handlers |

## Verify

```powershell
poetry run pytest tests/unit/test_api_skeleton.py -q
```

## Related

- [`curation-pii.md`](./curation-pii.md)
- [`architecture.md`](./architecture.md)
