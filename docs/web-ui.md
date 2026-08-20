# Web UI (Issue #18 / G18)

Mentorsuz tıklanabilir CuraNews arayüzü — tek sütun feed, konu filtresi, okundu butonu.

## Run

```powershell
docker compose up -d postgres redis
poetry run python scripts/seed_demo_users.py
poetry run python scripts/run_api.py
```

Open: http://127.0.0.1:8000/ui/  
(Port busy ise `$env:API_PORT=8001`)

## Features

| Feature | Behavior |
|---------|----------|
| Brand | `CuraNews` hero-level |
| User switch | demo-user-a / demo-user-b |
| Topic filter | client-side filter via `/topics` + item entities |
| Mark read | `POST /reads` then reload feed |
| API down | clear Turkish error banner |

## Files

| Path | Role |
|------|------|
| `web/index.html` | markup |
| `web/styles.css` | layout / motion |
| `web/app.js` | fetch feed/topics/reads |
| `api/app.py` | mounts `/ui` static + `/` → `/ui/` |

## Related

- [`fastapi-api.md`](./fastapi-api.md)
- [`api-feed-cache.md`](./api-feed-cache.md)
