# Day 19 evidence — Integration tests, live RSS, read grace (G19 / #19)

Staj defteri ek numaraları: **Ek-43, Ek-46, Ek-49** (üç asıl kanıt). İsteğe bağlı ek kareler aşağıda.

## Üç asıl kanıt

| Ek | What to capture |
|----|-----------------|
| **Ek-43** | `tests/integration/test_g19_acceptance.py` — §12.2 altı isim IDE’de açık (`test_backoff_increases` … `test_feed_shape`) |
| **Ek-46** | `src/curanews/scrapers/adapters/rss_catalog.py` + `rss.py` — resmi RSS katalog + parser |
| **Ek-49** | `src/curanews/api/feed_service.py` — `still_on_main_feed()` / `build_feed_response()` 20 dk grace |

## İsteğe bağlı kareler

| Ek | What to capture |
|----|-----------------|
| **Ek-44** | `poetry run pytest` tam yeşil terminal |
| **Ek-45** | `docs/testing.md` + `pytest -m integration -q` |
| **Ek-47** | `poetry run python scripts/refresh_news.py` JSON (`inserted` > 0) |
| **Ek-48** | Tarayıcı `/ui/` — canlı yayınevi başlıkları |
| **Ek-50** | Tarayıcı: Okundu yeşil kalır; 20 dk sonra Akış’tan düşer, Okunanlar’da durur |
| **Ek-51** | `poetry run pytest tests/unit/test_feed_inbox_grace.py tests/unit/test_rss_adapter.py -q` |

## Commands

```powershell
poetry run pytest
poetry run pytest tests/integration/test_g19_acceptance.py -v
poetry run pytest tests/unit/test_rss_adapter.py tests/unit/test_feed_inbox_grace.py -v

docker compose up -d postgres redis
poetry run alembic upgrade head
poetry run python scripts/refresh_news.py
$env:API_PORT=8001
poetry run python scripts/run_api.py
# open http://127.0.0.1:8001/ui/

$env:CURANEWS_LIVE_RSS="1"
poetry run pytest -m network -v
```

## Staj defteri (kopyala-yapıştır)

Aşağıdaki paragraf deftere uzun metin olarak yazılır; her iddia `bkz. Ek-N` ile bağlanır.

---

**Tarih:** 20 Ağustos 2026
**Görev:** G19 / Issue #19 — entegrasyon testleri; canlı RSS yolu; okundu haberlerin 20 dakika sonra ana akıştan düşmesi
**Dal:** `day-19-integration-tests`

Bugün CuraNews Aggregator stajında Faz 4’ün G19 günü tamamlandı. Planın §12.2 maddesi altı zorunlu test adını tek dosyada toplamayı, `pytest` komutunun Docker olmadan yeşil dönmesini ve ürünün gerçek haberle çalışmasını istiyordu. Önce regresyon ağı kuruldu: `tests/integration/test_g19_acceptance.py` içinde `test_backoff_increases`, `test_pii_masks_email`, `test_dedupe_same_url`, `test_curation_orders_differ_for_two_users`, `test_health_ok` ve `test_feed_shape` fonksiyonları plan isimleriyle birebir yazıldı (bkz. Ek-43). Varsayılan suite in-memory SQLite ve `tests/support/fakes.py` içindeki `FakeRedisClient` kullanıyor; `tests/support/db.py` seed yardımcıları ortak fixture’ları taşıyor. Marker’lar `pyproject.toml` içinde `unit` / `integration` / `redis` / `network` olarak sıkılandı (`--strict-markers`); canlı Redis ve canlı RSS isteğe bağlı skip ediliyor. Tek komut `poetry run pytest` veya `scripts/run_tests.py`.

İkinci iş, akışın GNews anahtarı olmadan boş kalmasıydı. Üretim yolu HTML kazıma değil, yayınevlerinin resmi RSS/Atom uçları oldu. Katalog `src/curanews/scrapers/adapters/rss_catalog.py` içindeki `DEFAULT_RSS_FEEDS` tuple’ında (BBC World/Türkçe, Guardian, NPR, Al Jazeera, AA, DW Türkçe, TRT Haber, A Haber, NTV, spor masaları) tutuluyor; host’lar `Settings.scrape_allowlist_hosts` ile allowlist’te (bkz. Ek-46). `RssAdapter` (`rss.py`) lxml ağacını `RawArticleDraft`’a çeviriyor; TRT Haber yorum düğümleri string olmadığı için etiket metni boş sayılıyor. `rss_client.py` içindeki round-robin, tek kaynağın (ör. BBC) kotayı doldurmasını engelliyor. Canlı yenileme `scripts/refresh_news.py`.

Üçüncü iş ürün davranışıydı: Okundu kartı hemen kaybolmasın, 20 dakika Akış’ta yeşil kalsın, sonra yalnızca Okunanlar’da dursun. `UserRepository.read_times()` `article_id → read_at` haritası döndürüyor; `feed_service.still_on_main_feed()` ve `build_feed_response()` stale okumaları `items` dışına alıp `read_items` arşivine koyuyor. Süre `READ_INBOX_GRACE_SECONDS=1200`. Kürasyon `hide_read=False` — ilgi profili silinmiyor. UI `web/app.js` içinde `stillOnMainFeed()` aynı pencereyi istemcide de uyguluyor (bkz. Ek-49).
