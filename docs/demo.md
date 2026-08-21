# Mentor demo script (Issue #20 / G20) — ~10 minutes

Aligned with `IMPLEMENTATION_PLAN.md` §13.2.

## Before the room

```powershell
docker compose up -d --build
# wait until api is healthy (~1–2 min first build)
poetry run python scripts/compose_smoke.py
```

Open: http://127.0.0.1:8001/ui/ and http://127.0.0.1:8001/docs

## Script

| Min | What to show | Talking point |
|-----|--------------|---------------|
| 0–1 | GitHub board / WIP | Scrumban: pull, WIP=2, Must vs Should |
| 1–3 | `docker compose ps` | Postgres + Redis + API; no secrets in Git (`.env.example` only) |
| 3–4 | `/docs` → `/health` | Contract is OpenAPI; health probes DB + Redis |
| 4–6 | UI Ada vs Deniz | Same catalog, different ranking after read bias |
| 6–7 | Okundu | Green for 20 min on Akış, then Okunanlar; profile kept |
| 7–8 | PII | `scrub_pii` masks email/phone/handle before store |
| 8–9 | Sources | Official RSS only; allowlist; no HTML scrape of news sites |
| 9–10 | Risks | ToS, Windows ports, Redis degrade path |

## Live commands (optional)

```powershell
# Refresh headlines inside/alongside stack
poetry run python scripts/refresh_news.py

# Local API without rebuilding (DB/Redis already up)
$env:API_PORT=8001
poetry run python scripts/run_api.py
```

## Acceptance snapshot

- [ ] Compose brings up api + db + redis
- [ ] `/health` shows `database: up`
- [ ] `/ui/` shows publisher headlines
- [ ] Ada and Deniz feeds differ after reads
- [ ] No real secrets committed
