# Testing strategy (Issue #19 / G19)

Regression net for CuraNews: unit → integration → optional live Redis.

## Pyramid

| Layer | Location | What it covers |
|-------|----------|----------------|
| Unit | `tests/unit/` | backoff, PII, adapters, RSS parser, Redis fake, curation helpers |
| Integration | `tests/integration/` | TestClient API, ingest dedupe, A≠B feed, cache HIT/MISS |
| Live Redis (optional) | `@pytest.mark.redis` | real Redis SET/GET/invalidate |
| Live RSS (optional) | `@pytest.mark.network` | BBC World HTTP (`CURANEWS_LIVE_RSS=1`) |

## One-command green

```powershell
poetry run pytest
# or
poetry run python scripts/run_tests.py
```

Filter by marker:

```powershell
poetry run pytest -m unit
poetry run pytest -m integration
poetry run pytest -m "not redis"
```

Live Redis (Docker Redis must be up):

```powershell
$env:CURANEWS_REDIS_URL = "redis://127.0.0.1:6379/0"
poetry run pytest -m redis
```

## G19 acceptance names (§12.2)

Defined in `tests/integration/test_g19_acceptance.py`:

1. `test_backoff_increases`
2. `test_pii_masks_email`
3. `test_dedupe_same_url`
4. `test_curation_orders_differ_for_two_users`
5. `test_health_ok`
6. `test_feed_shape`

```powershell
poetry run pytest tests/integration/test_g19_acceptance.py -v
```

## Design notes

- **No Docker required** for the default suite: SQLite in-memory + `FakeRedisClient`.
- API tests override `get_db` and `get_feed_cache` via FastAPI dependency overrides.
- Shared helpers live under `tests/support/` (DB seeders, FakeRedis).
- Markers are strict (`--strict-markers` in `pyproject.toml`).
- Live RSS: `CURANEWS_LIVE_RSS=1 poetry run pytest -m network` (hits BBC World). Default suite stays offline.
- Read grace: `still_on_main_feed()` keeps marked-read items on `/feed` `items` for `READ_INBOX_GRACE_SECONDS` (default 1200); older reads move to `read_items` (Okunanlar). See `tests/unit/test_feed_inbox_grace.py`.
