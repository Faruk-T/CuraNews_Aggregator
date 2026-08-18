# Day 17 evidence (Issue #17 / G17)

Staj defteri ek numaraları (öneri): **Ek-37 … Ek-42**.

## Code block screenshots (IDE)

| Ek | File | Focus |
|----|------|--------|
| **Ek-37** | `src/curanews/api/feed_service.py` | `build_feed_response()` HIT/MISS |
| **Ek-38** | `src/curanews/api/routers/feed.py` | `X-Cache` header |
| **Ek-39** | `src/curanews/api/routers/reads.py` | `invalidate_user` after read |
| **Ek-40** | `src/curanews/cache/feed_cache.py` | `invalidate_user()` |

## Terminal

| Ek | Capture |
|----|---------|
| **Ek-41** | `poetry run pytest tests/unit/test_api_feed_cache.py -q` yeşil |
| **Ek-42** | `verify_api_feed_cache.py` → miss→hit, after read → miss + top değişimi |

```powershell
docker compose up -d redis postgres
poetry run python scripts/seed_demo_users.py
poetry run pytest tests/unit/test_api_feed_cache.py -q
poetry run python scripts/run_api.py
# other terminal:
poetry run python scripts/verify_api_feed_cache.py
```
