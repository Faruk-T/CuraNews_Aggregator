# Day 20 evidence — Deploy + delivery (G20 / #20)

Staj defteri ek numaraları: **Ek-52, Ek-53, Ek-54**.

## Üç asıl kanıt

| Ek | What to capture |
|----|-----------------|
| **Ek-52** | `Dockerfile` + `docker-compose.yml` (`api` + `postgres` + `redis`) |
| **Ek-53** | Terminal: `docker compose up -d --build` then `compose_smoke.py` OK / `/health` |
| **Ek-54** | Browser: http://127.0.0.1:8001/ui/ live feed after Compose |

## Commands

```powershell
docker compose up -d --build
poetry run python scripts/compose_smoke.py
# open http://127.0.0.1:8001/ui/
# open http://127.0.0.1:8001/docs
```

## Staj defteri (kopyala-yapıştır)

**Tarih:** 21 Ağustos 2026  
**Görev:** G20 / Issue #20 — dağıtım ve staj teslim paketi  
**Dal:** `day-20-delivery`  
**Kanıtlar:** **Ek-52, Ek-53, Ek-54**

Bugün CuraNews Aggregator stajında Faz 4’ün son Must görevi olan **G20** tamamlandı. Amaç, mentorun veya temiz bir makinenin “Poetry bilmiyorum” demeden stack’i ayağa kaldırabilmesiydi. Önceki günlerde API host’ta Poetry + Docker Postgres/Redis ile çalışıyordu; `docker-compose.yml` yalnızca veritabanı ve cache içeriyordu. Bugün `Dockerfile` ile API imajı eklendi: Poetry bağımlılıkları, spaCy `en_core_web_sm`, Alembic migrasyonları ve `web/` static UI aynı imaja kopyalanıyor (bkz. Ek-52). `scripts/docker_entrypoint.py` Postgres hazır olana kadar bekliyor, `alembic upgrade head` çalıştırıyor, `CURANEWS_BOOTSTRAP=1` iken kaynak seed + RSS yenileme + demo kullanıcıları A/B yüklüyor, ardından `uvicorn curanews.api.app:app` dinliyor. Compose ağı içinde `DATABASE_URL` host adı `postgres:5432`, Redis `redis:6379`; host makinede Postgres hâlâ `5433` ile çakışmayı önlüyor.

Teslim dokümanları güncellendi: README beş adımlı quickstart, `docs/architecture.md` katman + Compose topolojisi, `docs/demo.md` on dakikalık mentor senaryosu (§13.2). Duman testi `scripts/compose_smoke.py` `/health` (database up) ve `/feed?user_id=demo-user-a` çağırıyor (bkz. Ek-53, Ek-54). Secret’lar yalnızca `.env.example`; gerçek `.env` gitignore’da. Bu paketle Must çıkış kapısı (tekrarlanabilir demo) kapanır.
