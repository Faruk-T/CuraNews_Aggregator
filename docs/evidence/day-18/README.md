# Day 18 evidence (Issue #18 / G18)

Staj defteri ek numaraları (öneri): **Ek-40, Ek-41, Ek-42** (Gün 17’den devam; defterinde numarayı sen hizala).

## Code / browser screenshots

| Ek | What | File / URL |
|----|------|------------|
| **Ek-40** | Kod SS | `web/app.js` — `loadFeed` / `markRead` |
| **Ek-41** | Tarayıcı SS | `http://127.0.0.1:8000/ui/` — CuraNews brand + feed list |
| **Ek-42** | Tarayıcı SS | API kapalıyken hata bandı **veya** “Okundu” sonrası sıra değişimi |

```powershell
poetry run pytest tests/unit/test_web_ui.py -q
poetry run python scripts/run_api.py
# browser: /ui/
```
