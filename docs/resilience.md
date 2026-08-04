# Resilience: Exponential Backoff (Day 7 / Issue #7)

Protect crawlers from bans and transient outages with **exponential backoff + jitter**
and per-source cooldowns.

## Formula

```text
delay = min(cap, base * 2**attempt) + U(0, jitter_ratio * expo)
```

Defaults (also in Settings): `base=0.5s`, `cap=60s`, `max_retries=5`, `jitter_ratio=0.2`.

## Retryable statuses

`408`, `429`, `500`, `502`, `503`, `504`

Non-retryable examples: `400`, `401`, `403`, `404`.

## Modules

| Module | Role |
|--------|------|
| `resilience/backoff.py` | Delay policy + status helper |
| `resilience/rate_limit.py` | Per-source cooldown registry |
| `resilience/retry.py` | `call_with_backoff()` wrapper |

## Demo check

```powershell
poetry run pytest tests/unit/test_backoff.py tests/unit/test_retry.py -q
```
