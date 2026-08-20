# Web UI (Issue #18 / G18; editorial refresh G19)

Kürate haber masası: karanlık editorial arayüz, öne çıkan haber, bento kart ızgarası,
konu chip’leri, arama, Ada/Deniz profilleri, skeleton yükleme ve kart animasyonları.

## Run

```powershell
docker compose up -d postgres redis
poetry run python scripts/refresh_news.py
poetry run python scripts/run_api.py
```

Open: http://127.0.0.1:8000/ui/  
(Port busy ise `$env:API_PORT=8001`)

## Features

| Feature | Behavior |
|---------|----------|
| Masthead | Animasyonlu CuraNews wordmark + canlı kicker |
| Personalar | Ada (ekonomi/AI) / Deniz (spor/iklim) → `demo-user-a/b` |
| Arama | Başlık, kaynak, konu üzerinde anlık filtre |
| Konu chip’leri | `/topics` + client-side filter |
| Öne çıkan | Akışın 1. haberi büyük kart |
| Izgara | Kalan haberler 2 sütun (mobilde 1) |
| Okundu | Kart **20 dakika** Akış’ta yeşil kalır, sonra Okunanlar’a geçer; `user_reads` silinmez |
| API down | Kırmızı toast; Türkçe hata |
| Motion | `prefers-reduced-motion` ile kapanır |

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
