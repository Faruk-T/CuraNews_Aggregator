# Day 12 evidence (Issue #12 / G12)

## Code block screenshots (IDE)

| File | Screenshot | Highlight |
|------|------------|-----------|
| `src/curanews/cache/feed_cache.py` | `code-feed-cache-hit-miss.png` | `get()` HIT/MISS/BYPASS logging |
| `src/curanews/cache/scrape_guard.py` | `code-scrape-lock.png` | `try_acquire_lock()` + cooldown |
| `src/curanews/cache/redis_client.py` | `code-redis-degrade.png` | unavailable degrade path |
| `docker-compose.yml` | `code-docker-redis.png` | `redis:7-alpine` service |

## Terminal (Ek-22 önerisi)

Single screenshot combining:

```powershell
docker compose up -d redis
poetry run pytest tests/unit/test_redis_cache.py -q
poetry run python scripts/verify_redis_cache.py --ttl 2
```

Show `MISS` → `HIT` → post-TTL `MISS` in JSON plus green pytest.

## Staj defteri

Reference HIT/MISS acceptance criteria, scrape lock/cooldown keys, and degrade behaviour when Redis is stopped.
