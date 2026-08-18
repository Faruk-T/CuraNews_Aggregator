# API ↔ Redis feed cache (Issue #17 / G17)

`GET /feed` uses Redis (`feed:{user_id}:{query_hash}`) and exposes HIT/MISS in JSON + `X-Cache`.
`POST /reads` invalidates that user's feed keys so the next request re-ranks.

## Flow

```text
GET /feed
  → FeedCache.get
      HIT  → return cached items (cache=hit, X-Cache: hit)
      MISS/BYPASS → CurationEngine.rank → SETEX → return (cache=miss|bypass)

POST /reads
  → UserRepository.record_read
  → FeedCache.invalidate_user(user_id)
```

## Run

```powershell
docker compose up -d postgres redis
poetry run python scripts/seed_demo_users.py
poetry run python scripts/run_api.py
# other terminal:
poetry run python scripts/verify_api_feed_cache.py
```

## Verify unit tests

```powershell
poetry run pytest tests/unit/test_api_feed_cache.py -q
```

## Related

- [`fastapi-api.md`](./fastapi-api.md)
- [`redis-cache.md`](./redis-cache.md)
- [`curation-pii.md`](./curation-pii.md)
