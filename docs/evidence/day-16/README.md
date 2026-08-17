# Day 16 evidence (Issue #16 / G16)

Staj defteri ek numaraları (öneri): **Ek-31 … Ek-36**.

## Code block screenshots (IDE)

| Ek | File | Class / focus |
|----|------|----------------|
| **Ek-31** | `src/curanews/api/app.py` | `create_app()` — router mount |
| **Ek-32** | `src/curanews/api/schemas.py` | `HealthResponse`, `FeedResponse`, `ReadCreate` |
| **Ek-33** | `src/curanews/api/routers/health.py` | `GET /health` |
| **Ek-34** | `src/curanews/api/routers/feed.py` | `GET /feed` + `CurationEngine` |

## Terminal / browser

| Ek | What to capture |
|----|-----------------|
| **Ek-35** | `poetry run pytest tests/unit/test_api_skeleton.py -q` yeşil |
| **Ek-36** | Browser: `/docs` OpenAPI (health, articles, feed, reads) + `/health` 200 JSON |

```powershell
poetry run pytest tests/unit/test_api_skeleton.py -q
poetry run python scripts/run_api.py
# browser: http://127.0.0.1:8000/docs  and  /health
```

## Staj defteri

Her iddiayı `bkz. Ek-31` … `bkz. Ek-36` ile bağla.
