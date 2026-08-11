# Redis cache (Issue #12 / G12)

Redis backs hot-path caching and scrape coordination per `IMPLEMENTATION_PLAN` §6.5.

## Run locally

```powershell
docker compose up -d redis
```

Ensure `.env` includes:

```env
REDIS_URL=redis://localhost:6379/0
FEED_CACHE_TTL_SECONDS=120
```

## Verify

```powershell
poetry run pytest tests/unit/test_redis_cache.py -q
poetry run python scripts/verify_redis_cache.py --ttl 2
```

Expected demo JSON:

- `initial` lookup → `MISS`
- `after_set` lookup → `HIT`
- `after_ttl_wait` lookup → `MISS` (TTL expired)
- scrape lock: first acquire `true`, second `false`; cooldown `true`

## Key contract

| Key pattern | TTL | Purpose |
|-------------|-----|---------|
| `feed:{user_id}:{query_hash}` | `FEED_CACHE_TTL_SECONDS` (default 120) | Personal feed cache |
| `scrape:lock:{source_id}` | job duration (default 300s) | Prevent parallel scrapes |
| `scrape:cooldown:{source_id}` | post-429 window (default 120s) | Source cooldown |

## Modules

| Module | Role |
|--------|------|
| `cache/redis_client.py` | Connection wrapper; logs and degrades when Redis is down |
| `cache/feed_cache.py` | Feed get/set/invalidate with `HIT` / `MISS` / `BYPASS` logging |
| `cache/scrape_guard.py` | Lock + cooldown helpers |

When Redis is unavailable, feed lookups return `BYPASS` and scrape locks are **best-effort allowed** so CLI/API paths stay up (slower, without shared coordination).

## Related

- [`architecture.md`](./architecture.md)
- [`postgresql-schema.md`](./postgresql-schema.md)
