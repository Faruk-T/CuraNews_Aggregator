# CuraNews-Aggregator — Ana Uygulama Planı (Master Implementation Plan)

> **Proje adı:** CuraNews-Aggregator  
> **Tam adı:** Sosyal Medya ve Web Destekli Dinamik Haber Agregatörü  
> **Süre:** 20 iş günü (staj dönemi)  
> **SDLC:** Agile → **Scrumban** (Scrum ritüelleri + Kanban akış / WIP / Pull)  
> **Planlama:** Kova Tipi Planlama (Bucket Size Planning) + Çekme Prensibi (Pull Principle)  
> **Belge rolü:** Bu dosya, projeyi okuyan herkesin mimariye, sürece, veri modeline, API’ye ve 20 göreve **sonuna kadar hâkim** olmasını hedefler.  
> **Takip:** Her görev `[ ]` ile işaretlenir; bitince `[x]` yapılır.  
> **Sürüm:** 2.6 · **Tarih:** 2026-08-04 · **Durum:** Gün 6 (Issue #6) Playwright dynamic scrape — commit kullanıcıda  
> **GitHub:** https://github.com/Faruk-T/CuraNews_Aggregator

---

## İçindekiler

1. [Yönetici Özeti](#1-yönetici-özeti)
2. [Problem, Vizyon ve Başarı Kriterleri](#2-problem-vizyon-ve-başarı-kriterleri)
3. [Kapsam: Dahil / Hariç / Varsayımlar](#3-kapsam-dahil--hariç--varsayımlar)
4. [Scrumban Proje Yönetimi (SDLC)](#4-scrumban-proje-yönetimi-sdlc)
5. [Sistem Mimarisi (Derinlemesine)](#5-sistem-mimarisi-derinlemesine)
6. [Teknoloji Yığını ve Karar Kayıtları](#6-teknoloji-yığını-ve-karar-kayıtları)
7. [Veri Modeli, Sözleşmeler ve Algoritmalar](#7-veri-modeli-sözleşmeler-ve-algoritmalar)
8. [Güvenlik, Gizlilik (PII) ve Etik Kazıma](#8-güvenlik-gizlilik-pii-ve-etik-kazıma)
9. [Dizin Yapısı ve Modül Sorumlulukları](#9-dizin-yapısı-ve-modül-sorumlulukları)
10. [20 Günlük Takvim (Gün Gün)](#10-20-günlük-takvim-gün-gün)
11. [Fazlar ve 20 Görev (Detaylı Issue Spec)](#11-fazlar-ve-20-görev-detaylı-issue-spec)
12. [Test, Kalite ve CI Stratejisi](#12-test-kalite-ve-ci-stratejisi)
13. [Dağıtım, Demo ve Teslim Paketi](#13-dağıtım-demo-ve-teslim-paketi)
14. [Risk Kaydı, MoSCoW ve Escalation](#14-risk-kaydı-moscow-ve-escalation)
15. [Sözlük (Glossary)](#15-sözlük-glossary)
16. [İlerleme Panosu](#16-ilerleme-panosu)
17. [Sonraki Adım](#17-sonraki-adım)

---

## 1. Yönetici Özeti

CuraNews-Aggregator, birden fazla **web haber kaynağı** ve (mümkün/izinli olduğu ölçüde) **sosyal medya akışlarından** içerik toplayan; bu içeriği **normalize eden, tekilleştiren, NLP ile etiketleyen**, kullanıcı okuma geçmişine göre **algoritmik olarak kürasyonlayan** ve sonuçları **REST API + web arayüzü** üzerinden sunan bir sistemdir.

Rastgele haber listesi **yoktur**. Her feed yanıtı şu sinyallerin birleşiminden üretilir:

- Kullanıcının geçmişte okuduğu konular / entity’ler (ilgi profili)
- Haberin tazeliği (recency)
- Kaynak çeşitliliği (tek kaynaktan doygunluğu kırma)
- İçerik kalitesi / eksik alan cezası (başlık yoksa düşük skor)

Sistem **20 iş gününde** 4 milestone (kova) ile teslim edilir. Yönetim **Waterfall değildir**: gereksinimler faz sonunda gözden geçirilir; iş **itilmez**, kapasite kadar **çekilir**; aynı anda en fazla **2** aktif iş (WIP) vardır.

| Katman | Teknoloji (hedef) |
|--------|-------------------|
| Statik kazıma | Scrapy + BeautifulSoup |
| Dinamik / JS / infinite scroll | Playwright (async) |
| Kalıcı depo | PostgreSQL |
| Önbellek / scrape kilidi | Redis |
| NLP / entity | spaCy |
| API | FastAPI (tercih; alternatif Flask) |
| Bağımlılık kilidi | Poetry **veya** pip-tools |
| Çalıştırma | Docker Compose (Postgres + Redis + API) |

---

## 2. Problem, Vizyon ve Başarı Kriterleri

### 2.1 Problem

Günlük haber tüketimi dağınıktır:

- Kullanıcı onlarca site ve sosyal akış arasında gezinir.
- Aynı haber farklı sitelerde tekrarlanır (gürültü).
- Sosyal medya içerikleri kişisel veri (PII) taşıyabilir.
- Ham kazıma, bot koruması ve API limitleri yüzünden kırılgandır.
- “Her şeyi göster” yaklaşımı kullanıcıyı yorar; kişiselleştirme çoğu staj projesinde yoktur.

### 2.2 Vizyon (tek cümle)

> **CuraNews**, güvenilir kaynaklardan etik biçimde topladığı haberleri NLP ile anlamlandırır; kullanıcının okuma geçmişine göre sıralar; kişisel veriyi koruyarak hızlı bir API ve sade bir arayüzle sunar.

### 2.3 Kullanıcı Persona’ları

| Persona | İhtiyaç | Sistem yanıtı |
|---------|---------|---------------|
| **Okuyucu (primary)** | İlgilendiği konularda güncel, tekrarsız haber | Kürasyonlu `/feed` |
| **Staj mentoru / değerlendirici** | Mimariyi, süreci ve çalışan demoyu görmek | Bu plan + Scrumban panosu + Docker demo |
| **Geliştirici (stajyer)** | Net görev, DoR/DoD, düşük bağlam kaybı | G1–G20 issue spec’leri |

### 2.4 Başarı Kriterleri (projeyi “bitti” saymak için)

Staj sonunda aşağıdaki **hepsinin** sağlanması beklenir:

1. En az **1 statik** (Scrapy/BS4) ve **1 dinamik** (Playwright) kaynak adaptörü çalışır.
2. Haberler **PostgreSQL**’de kalıcıdır; tekrar çekimde **dedupe** olur.
3. **Redis** en az bir hot-path’te (feed cache veya scrape cooldown) kullanılır.
4. **spaCy** ile entity/konu etiketleri üretilir ve saklanır.
5. İki farklı okuma geçmişi **farklı sıralı** feed üretir (kürasyon kanıtı).
6. Sosyal/ham metinde örnek PII **maskelenmiş** görünür.
7. **FastAPI** üzerinden OpenAPI docs ile uçlar çağrılabilir.
8. Minimal web UI ile liste + okundu işareti çalışır.
9. `docker compose up` (veya eşdeğer) ile üçüncü kişi demoyu ayağa kaldırabilir.
10. Bu plandaki Must görevler `[x]` ve Scrumban panosu günceldir.

### 2.5 Ölçülebilir Kalite Hedefleri (hedef, sert SLA değil)

| Metrik | Hedef (staj) |
|--------|----------------|
| Feed p95 (cache hit) | < 200 ms (lokal) |
| Feed p95 (cache miss) | < 1.5 s (lokal, küçük veri) |
| Dedupe doğruluğu | Aynı canonical URL → tek kayıt |
| Test | Kritik path için otomatik test yeşil |
| WIP ihlali | Haftada ≤ 1 (retro’da işlenir) |

---

## 3. Kapsam: Dahil / Hariç / Varsayımlar

### 3.1 Dahil (In Scope)

- Statik haber sitesi kazıma (Scrapy + BS4)
- JS ağırlıklı / scroll gerektiren sayfa kazıma (Playwright)
- Exponential backoff + kaynak başına rate limit
- PostgreSQL şeması + migration
- Redis cache / lock
- spaCy NER + konu etiketleme
- Algoritmik kürasyon (kural + skor tabanlı; derin öğrenme şart değil)
- PII pseudonymization / masking
- FastAPI REST + minimal frontend
- Docker Compose ile lokal/demo dağıtım
- Scrumban panosu ve bu master plan

### 3.2 Hariç (Out of Scope — 20 gün)

- Mobil native uygulama
- Gerçek zamanlı WebSocket ölçekli streaming
- Üretim-grade Kubernetes / multi-region
- Tam Observability (Prometheus/Grafana zorunlu değil; temel log yeter)
- Sosyal platformlara login gerektiren özel API entegrasyonları (ToS riski)
- Çok dilli üretim NLP pipeline’ı (TR/EN’den biri veya küçük model ile başlanır)
- Reklam / monetizasyon
- Kullanıcı auth’un OAuth/SSO ile tam kurumsal hali (basit kullanıcı kimliği yeterli)

### 3.3 Varsayımlar

- Geliştirici tek kişidir (stajyer); mentor review yapar.
- Python **3.11+** kullanılabilir.
- Docker Desktop (veya eşdeğer) kurulabilir.
- Kazıma yalnızca **kamuya açık** veya açıkça izinli içerikte yapılır.
- Sosyal medya için gerekirse **mock HTML/fixture** veya izinli demo sayfası kabul edilir (ToS engelinde).
- FastAPI tercih edilir; mentor isterse Flask’a geçiş Faz 1 sonunda kararlaştırılır.

### 3.4 Kısıtlar

- 20 iş günü sert üst sınırdır.
- WIP = 2 (tek kişi için multitasking yasağı).
- Secret’lar asla Git’e girmez.
- “Çalışıyor gibi görünen ama yeniden üretilemeyen” demo kabul edilmez (pinning + README zorunlu).

---

## 4. Scrumban Proje Yönetimi (SDLC)

### 4.1 Neden Waterfall Değil?

Waterfall; gereksinim → tasarım → kod → test zincirini kilitler. Bu projede:

- Hedef sitelerin HTML’i değişebilir.
- Anti-bot kuralları sürpriz yaratır.
- spaCy model boyutu / kurulum sürtünmesi çıkabilir.
- Mentor geri bildirimi faz sonunda yön değiştirebilir.

Bu yüzden **Agile** seçilir; somut çerçeve **Scrumban**’dır.

### 4.2 Scrumban Nedir? (Bu Projeye Uyarlanmış)

Scrumban = Scrum’ın hafif ritüelleri + Kanban’ın görsel akış, **WIP limitleri** ve **pull** sistemi.

Bu projede **olmazsa olmaz** unsurlar:

1. **WIP limitleri** (kolon bazlı) — yoksa Scrumban değil, süslü to-do listesidir.
2. **Pull** — iş atanmaz; kapasite açılınca Ready’den çekilir.
3. **On-demand planning** — Ready eşiğin altına düşünce planlama tetiklenir.
4. **Bucket-size planning** — uzun vadeli iş ufukları (aşağıda 20 güne uyarlandı).
5. **Kısa cadans** — 5 günlük kovalar + daily + review/retro.

Kaynak çerçeve özeti: Scrumban’da WIP ve pull yük taşıyan parçadır; bucket planning 1-yıl / 6-ay / 3-ay ufuklarını temsil eder; on-demand planning Ready eşiği ile tetiklenir ([Rock Scrumban](https://www.rock.so/blog/scrumban), [Ora Scrumban Guide](https://ora.pm/blog/scrumban), [Atlassian Scrumban](https://www.atlassian.com/agile/project-management/scrumban)).

### 4.3 Kova Tipi Planlama — 20 Güne Uyarlama

Klasik Scrumban kovaları (1y / 6ay / 3ay) buraya **sıkıştırılır**:

| Klasik kova | Bu projedeki karşılık | İçerik |
|-------------|----------------------|--------|
| 1-year (Vizyon) | **Vizyon Kovası** | Ürün vizyonu, non-goals, başarı kriterleri (bu belgenin §2–3) |
| 6-month (Gereksinim) | **Gereksinim Kovası** | 4 Faz (Milestone), mimari kararlar, ADR’ler |
| 3-month (Görev) | **Yürütme Kovası** | G1–G20 issue’ları; Ready’ye sadece buradan alınır |
| Board | **Scrumban Tahtası** | Ready → In Progress → Review → Done |

**Kural:** On-demand planning sırasında yeni iş **yalnızca Yürütme Kovası’ndan** (G1–G20 + gerekirse parçalanmış alt kartlar) Ready’ye alınır. Vizyon kovasına “yeni fikir” eklemek serbesttir; doğrudan In Progress’e atmak yasaktır.

### 4.4 4 Milestone = 4 Zaman Kovası (Cadans)

| Kova | Günler | Milestone | Tema | Ana teslim |
|------|--------|-----------|------|------------|
| B1 | 1–5 | Faz 1 | Foundation | Repo, pano, pinning, Scrapy iskeleti |
| B2 | 6–10 | Faz 2 | Acquisition Resilience | Playwright, adapter, backoff |
| B3 | 11–15 | Faz 3 | Intelligence & Store | Postgres, Redis, NLP, kürasyon, PII |
| B4 | 16–20 | Faz 4 | Productize | API, UI, test, deploy |

Bir kova bitmeden sonraki kovadan iş çekilmez (P0 blocker hariç; mentor onayı ile).

### 4.5 Scrumban Tahtası

```
[ Vizyon ] [ Gereksinim/Fazlar ] [ Yürütme: G1–G20 ]
                    │
                    ▼ (on-demand planning)
┌─────────┬─────────┬────────────────┬─────────┬─────────┐
│ Backlog │ Ready   │ In Progress    │ Review  │ Done    │
│ (WIP ∞) │ (WIP≤5) │ (WIP≤2)        │ (WIP≤2) │ (∞)     │
└─────────┴─────────┴───────┬────────┴─────────┴─────────┘
                            │
                     ┌──────▼──────┐
                     │   Blocked   │  (WIP sayılmaz; engel notu zorunlu)
                     └─────────────┘
```

| Kolon | WIP | Açıklama |
|-------|-----|----------|
| Backlog | — | Henüz DoR karşılamayan / düşük öncelikli |
| Ready | ≤ 5 | DoR tamam; pull adayı |
| In Progress | **≤ 2** | Aktif kodlama |
| Review | ≤ 2 | Self-review / mentor PR |
| Blocked | — | Dış engel; sebep + sonraki kontrol tarihi |
| Done | — | DoD karşılandı |

**Planning trigger:** Ready < 3 kart → 15–30 dk on-demand planning (Yürütme kovasından doldur).

### 4.6 Çekme Prensibi (Pull) — Operasyonel Kurallar

1. Kart **Ready**’de değilse çekilemez.
2. `In Progress` doluysa (2 kart) yeni kart çekilemez; bitir veya Blocked’a al.
3. Mentor “şunu da yap” dese bile — önce Ready’ye yazılır, WIP uygunsa çekilir (**push yasağı**).
4. Bitince kart Review’a gider; DoD checklist işaretlenmeden Done olmaz.
5. Her Done kartında bu dosyadaki ilgili `[ ]` → `[x]` güncellenir (tek doğruluk kaynağı).

### 4.7 Ritüeller

| Ritüel | Ne zaman | Süre | Gündem |
|--------|----------|------|--------|
| Daily | Her iş günü başı | 5–10 dk | Dün / bugün / engel / WIP sayısı |
| On-demand Planning | Ready < 3 | 15–30 dk | DoR, öncelik, parçalama |
| Bucket Review | Her faz sonu (5. gün) | 20–30 dk | Demo, kabul, taşınacak iş |
| Retro | Her faz sonu | 15 dk | WIP ihlali, tooling, risk, hız |

### 4.8 Definition of Ready (DoR)

Bir kart Ready’ye alınmadan önce:

- [ ] Tek cümlelik amaç var
- [ ] Kabul kriterleri (Given/When/Then veya madde listesi) var
- [ ] Bağımlılıklar listelenmiş (G# veya dış sistem)
- [ ] Efor ≤ 1 gün; değilse alt kartlara bölünmüş
- [ ] Test / doğrulama yöntemi yazılmış
- [ ] Hangi faz/kova olduğu etiketlenmiş

### 4.9 Definition of Done (DoD)

- [ ] Lokal çalışır (komut README’de)
- [ ] En az smoke test veya manuel doğrulama notu (tarihli)
- [ ] Tip / lint kırığı yok (proje standardı oluştuktan sonra)
- [ ] Secret commit edilmedi
- [ ] İlgili dokümantasyon güncellendi
- [ ] IMPLEMENTATION_PLAN.md checkbox güncellendi
- [ ] Review kolonundan geçti (self veya mentor)

### 4.10 Issue Etiketleri (öneri)

- `type:chore` · `type:feature` · `type:fix` · `type:docs` · `type:spike`
- `milestone:faz-1` … `milestone:faz-4`
- `priority:must|should|could`
- `area:scrape|db|nlp|api|ui|ops`

---

## 5. Sistem Mimarisi (Derinlemesine)

### 5.1 Mimari Tarz

- **Modüler monolit** (20 gün için doğru denge): tek deployable API + ayrı çalışan scraper job’ları.
- Sınırlar **modül paketleri** ile çizilir (`scrapers`, `browser`, `db`, `cache`, `nlp`, `privacy`, `api`).
- İleride mikroservise bölünmeye gerek yoktur; adapter arayüzleri yine de gevşek bağ kurar.

### 5.2 Bağlam Diyagramı (C4 Level 1)

```
                    ┌──────────────┐
                    │   Okuyucu    │
                    └──────┬───────┘
                           │ HTTPS
                    ┌──────▼───────┐
                    │  Web UI      │
                    └──────┬───────┘
                           │ REST/JSON
┌─────────────┐     ┌──────▼───────┐     ┌─────────────────┐
│ Haber       │◀───▶│ CuraNews     │◀───▶│ PostgreSQL      │
│ Siteleri    │     │ Backend      │     └─────────────────┘
└─────────────┘     │ (API+Jobs)   │     ┌─────────────────┐
┌─────────────┐     │              │◀───▶│ Redis           │
│ Sosyal / JS │◀───▶│              │     └─────────────────┘
│ Sayfalar    │     └──────────────┘
└─────────────┘
```

### 5.3 Konteyner / Bileşen Görünümü

| Bileşen | Çalışma şekli | Girdi | Çıktı |
|---------|---------------|-------|-------|
| **StaticScraper** (Scrapy/BS4) | CLI job / cron | kaynak URL listesi | `RawArticle[]` |
| **DynamicScraper** (Playwright) | async worker | JS sayfa URL | `RawArticle[]` |
| **Resilience** | library | HTTP hataları | retry/delay kararları |
| **IngestionService** | pipeline | RawArticle | DB satırı + cache invalidate |
| **NlpService** | pipeline adımı | title+summary+body | entities/tags |
| **PrivacyService** | pipeline adımı | ham metin | scrubbed metin |
| **CurationEngine** | API path | user_id + aday haberler | sıralı feed |
| **API** (FastAPI) | HTTP sunucu | REST | JSON |
| **Web** | statik veya basit SPA | tarayıcı | UI |

### 5.4 Uçtan Uca Sequence (Ingestion)

```
Scheduler/CLI → Adapter.fetch()
             → Resilience.wrap(request)
             → RawArticle[]
             → Privacy.scrub()
             → Normalize + Hash
             → Dedupe (DB unique)
             → Persist (Postgres)
             → Nlp.extract() → tags
             → Cache.invalidate(feed:*)
```

### 5.5 Uçtan Uca Sequence (Personalized Feed)

```
UI → GET /feed?user_id=...
   → Redis GET feed:{user_id}:{filter_hash}
      hit? → return
      miss → Postgres aday set
          → CurationEngine.score()
          → top-K
          → Redis SETEX
          → return
```

### 5.6 Hata ve Dayanıklılık Sınırları

| Senaryo | Davranış |
|---------|----------|
| 429 / 503 | Exponential backoff + jitter; max_retries aşınca job fail, DLQ/log |
| Timeout | Retry politikası; kaynak cooldown Redis’e yazılır |
| Parse kırılması | Item drop + error metric/log; tüm job’u öldürme |
| NLP model yok | Graceful degrade: tags boş, ingestion devam |
| Redis down | Feed DB’den gelir (yavaş ama ayakta); scrape lock best-effort |
| Postgres down | API 503; scraper durur |

### 5.7 “Neden Mikroservis Değil?”

20 günde network sınırı, ayrı deploy, distributed tracing maliyeti getirir. Adapter + service katmanı ile **ileride bölünebilir** monolit yeterlidir. Bu bir ADR kararıdır (aşağıda ADR-001).

---

## 6. Teknoloji Yığını ve Karar Kayıtları

### 6.1 Yığın Tablosu

| Alan | Seçim | Alternatif | Neden seçildi |
|------|-------|------------|---------------|
| Dil | Python 3.11+ | — | Scrapy, spaCy, Playwright ekosistemi |
| Statik scrape | Scrapy + BS4 | yalnız requests | Pipeline/middleware + güçlü selector |
| Dinamik scrape | Playwright async | Selenium | Daha modern async API, hızlı/stabil |
| API | **FastAPI** | Flask | Async, Pydantic, otomatik OpenAPI |
| ORM | SQLAlchemy 2.x + Alembic | Tortoise | Olgun migration |
| DB | PostgreSQL 16 | SQLite | Gerçekçi üretim benzeri; JSON/index |
| Cache | Redis 7 | in-memory dict | Paylaşımlı lock + TTL; demo’da Compose |
| NLP | spaCy (`xx_ent_wiki_sm` veya `en_core_web_sm` / TR modeli uygunsa) | NLTK yalnız | NER üretimi hazır |
| Pinning | Poetry **veya** pip-tools | serbest pip | Reprodüksiyon |
| Test | pytest + httpx | — | FastAPI uyumu |
| Paketleme | Docker Compose | yalnız venv | Mentor demosu |

### 6.2 Architecture Decision Records (ADR)

#### ADR-001 — Modüler monolit
- **Durum:** Kabul
- **Karar:** Tek Python paketi `curanews`, sınırlı modüller.
- **Sonuç:** Hızlı geliştirme; ileride worker ayrı process olabilir.

#### ADR-002 — FastAPI tercihi
- **Durum:** Kabul (Faz 1 sonunda teyit)
- **Karar:** Varsayılan API FastAPI.
- **Sonuç:** `/docs` mentor için hazır demo yüzeyi.

#### ADR-003 — Önce polite public kaynaklar
- **Durum:** Kabul
- **Karar:** Login/CAPTCHA zorunlu sosyal akışlar Must değil; fixture ile Playwright deseni kanıtlanır.
- **Sonuç:** Etik ve yasal risk düşer; öğrenme hedefi korunur.

#### ADR-004 — Kürasyon = açıklanabilir skor
- **Durum:** Kabul
- **Karar:** ML ranker yok; ağırlıklı skor formülü + okuma geçmişi vektörü.
- **Sonuç:** Debug edilebilir, staj raporuna yazılabilir.

#### ADR-005 — Dependency pinning zorunlu
- **Durum:** Kabul
- **Karar:** Poetry lock **veya** pip-tools `requirements.txt` commit.
- **Sonuç:** “Bende çalışıyor” eliminasyonu.

### 6.3 Scrapy vs Playwright Karar Ağacı

```
Kaynak sayfası JS olmadan tam içerik veriyor mu?
  Evet → Scrapy + BS4
  Hayır → İçerik scroll/XHR sonrası mı geliyor?
            Evet → Playwright (scroll strategy)
            Hayır → robots/ToS engeli var mı?
                      Evet → kaynak listeden çıkar / mock
                      Hayır → Playwright network idle + selector
```

### 6.4 Exponential Backoff Formülü

\[
delay = \min(cap,\ base \times 2^{attempt}) + U(0, jitter)
\]

Öneri başlangıç değerleri:

- `base = 0.5s`
- `cap = 60s`
- `max_retries = 5`
- `jitter = 0.2 * delay`

Retry yapılacak durumlar: `408, 429, 500, 502, 503, 504`, bağlantı hataları.  
Retry yapılmayacak: `400, 401, 403, 404` (kaynak politikası ayrı ele alınır).

### 6.5 Redis Anahtar Sözleşmesi

| Anahtar | TTL | Amaç |
|---------|-----|------|
| `feed:{user_id}:{query_hash}` | 60–300s | Kişisel feed cache |
| `scrape:lock:{source_id}` | job süresi | Aynı kaynağı paralel kazımama |
| `scrape:cooldown:{source_id}` | 60–900s | 429 sonrası soğuma |
| `article:hot:{id}` | 300s | Tekil haber cache (opsiyonel) |

---

## 7. Veri Modeli, Sözleşmeler ve Algoritmalar

### 7.1 ER Diyagramı (mantıksal)

```
sources 1───* articles *───* entities
                │
                │ 1
                │
                * user_reads *───1 users
```

### 7.2 Tablo Taslakları

#### `users`
| Kolon | Tip | Not |
|-------|-----|-----|
| id | UUID PK | |
| external_key | TEXT UNIQUE | staj için basit kullanıcı anahtarı |
| created_at | TIMESTAMPTZ | |

#### `sources`
| Kolon | Tip | Not |
|-------|-----|-----|
| id | UUID PK | |
| name | TEXT | |
| base_url | TEXT | |
| kind | ENUM(`static`,`dynamic`) | adapter seçimi |
| enabled | BOOL | |
| robots_respected | BOOL | |
| created_at | TIMESTAMPTZ | |

#### `articles`
| Kolon | Tip | Not |
|-------|-----|-----|
| id | UUID PK | |
| source_id | FK | |
| url | TEXT | |
| url_hash | CHAR(64) UNIQUE | sha256(canonical_url) |
| title | TEXT | |
| summary | TEXT | scrubbed |
| body | TEXT NULL | scrubbed |
| author_display | TEXT NULL | **pseudonymized** |
| published_at | TIMESTAMPTZ NULL | |
| scraped_at | TIMESTAMPTZ | |
| content_hash | CHAR(64) | dedupe yardımcı |
| language | TEXT NULL | |
| raw_metadata | JSONB | PII tutulmaz |

#### `entities`
| Kolon | Tip | Not |
|-------|-----|-----|
| id | UUID PK | |
| label | TEXT | örn. `ORG:OpenAI` |
| ent_type | TEXT | PERSON/ORG/GPE/TOPIC… |
| normalized | TEXT | lowercase/slug |

#### `article_entities`
| article_id | entity_id | confidence | UNIQUE(article_id, entity_id) |

#### `user_reads`
| user_id | article_id | read_at | dwell_ms NULL | UNIQUE(user_id, article_id) |

### 7.3 Domain Nesneleri (Pydantic taslak)

```python
class RawArticle(BaseModel):
    source_key: str
    url: str
    title: str
    summary: str | None = None
    body: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    metadata: dict[str, Any] = {}

class ArticleDTO(BaseModel):
    id: UUID
    title: str
    summary: str | None
    url: str
    source_name: str
    published_at: datetime | None
    entities: list[str]
    score: float | None = None  # feed'de
```

### 7.4 SourceAdapter Sözleşmesi

```python
class SourceAdapter(Protocol):
    source_id: str
    kind: Literal["static", "dynamic"]

    async def fetch(self, *, limit: int = 50) -> list[RawArticle]:
        """Kaynaktan ham maddeleri çeker; exception fırlatabilir."""
```

Static ve Dynamic adaptörler aynı sözleşmeyi uygular → Ingestion tek pipeline.

### 7.5 Algoritmik Kürasyon Skoru

Aday haber \(a\), kullanıcı profili \(u\) için:

\[
score(a,u) =
w_t \cdot freshness(a) +
w_i \cdot interest(a,u) +
w_d \cdot diversity(a, recent_feed) -
w_p \cdot penalty(a)
\]

**Önerilen ağırlıklar (başlangıç):**

| Sembol | Anlam | Varsayılan |
|--------|-------|------------|
| \(w_t\) | tazelik | 0.30 |
| \(w_i\) | ilgi (entity overlap) | 0.45 |
| \(w_d\) | çeşitlilik | 0.15 |
| \(w_p\) | ceza | 0.10 |

**freshness:** \(e^{-\lambda \Delta t}\) (\(\Delta t\) saat; \(\lambda \approx 0.02\))  
**interest:** Jaccard veya cosine benzerliği (kullanıcının okuduğu entity frekans vektörü ↔ haber entity seti)  
**diversity:** son K öneride aynı `source_id` tekrarlıyorsa 0’a yaklaşır  
**penalty:** title boş, summary çok kısa, entity yok → artar

**Kritik kabul kanıtı:** User A (ekonomi ağırlıklı okumuş) ile User B (spor) aynı aday havuzunda farklı sıralama görmeli.

### 7.6 REST API Sözleşmesi (hedef)

| Method | Path | Açıklama |
|--------|------|----------|
| GET | `/health` | liveness; db/redis durumu |
| GET | `/articles` | sayfalı liste; filtre: source, tag, q |
| GET | `/articles/{id}` | detay |
| GET | `/topics` | popüler entity/topic |
| GET | `/feed` | kişiselleştirilmiş; `user_id` zorunlu |
| POST | `/reads` | `{user_id, article_id}` okundu sinyali |
| POST | `/jobs/scrape/{source_key}` | (dev) manuel tetik — prod’da korumalı |

**Örnek `GET /feed` yanıtı:**

```json
{
  "user_id": "demo-user-a",
  "generated_at": "2026-07-27T10:00:00Z",
  "cache": "miss",
  "items": [
    {
      "id": "...",
      "title": "...",
      "summary": "...",
      "url": "https://...",
      "source_name": "ExampleNews",
      "entities": ["ORG:Example", "TOPIC:economy"],
      "score": 0.82
    }
  ]
}
```

### 7.7 Ortam Değişkenleri (`.env.example` taslağı)

```
APP_ENV=dev
LOG_LEVEL=INFO
DATABASE_URL=postgresql+psycopg://curanews:curanews@localhost:5432/curanews
REDIS_URL=redis://localhost:6379/0
SPACY_MODEL=en_core_web_sm
FEED_CACHE_TTL_SECONDS=120
SCRAPE_MAX_RETRIES=5
SCRAPE_BACKOFF_BASE=0.5
SCRAPE_CONCURRENCY=2
API_HOST=0.0.0.0
API_PORT=8000
PII_HASH_SALT=change-me-in-local-only
```

---

## 8. Güvenlik, Gizlilik (PII) ve Etik Kazıma

### 8.1 PII Politikası

| Veri | Tutum |
|------|-------|
| E-posta, telefon, TC/kimlik benzeri | Regex ile tespit → maskele (`***`) veya saklama |
| Sosyal kullanıcı adı | HMAC-SHA256(salt + username) ile **pseudonymize**; ham yazma |
| Profil URL | Saklama veya hash |
| Haber içeriğindeki kişi adları (NER PERSON) | Haber bağlamında kalabilir; sosyal handle ile karıştırma |

**Pseudonymization ≠ Encryption:** Geri dönüş salt ile kontrollüdür; üretim salt’ı secret’tır, Git’e girmez.

### 8.2 Etik / Yasal Kazıma Kuralları

1. `robots.txt` mümkün olduğunca okunur ve sayılır.
2. Düşük concurrency (varsayılan 2).
3. Tanıtıcı User-Agent: `CuraNewsBot/0.1 (+mailto:staj@example.com)` (gerçek iletişim bilgisini mentorla netleştir).
4. Login duvarı / CAPTCHA aşma **yapılmaz**.
5. ToS açıkça yasaklıyorsa kaynak **Won’t**’a alınır; Playwright deseni fixture ile gösterilir.
6. Toplanan veri staj demo’su içindir; ticari yeniden yayın varsayılmaz.

### 8.3 Uygulama Güvenliği (minimum)

- Secret’lar `.env` + Compose secrets
- `/jobs/scrape` gibi yazma uçları `APP_ENV=dev` iken açık, aksi halde token
- SQLAlchemy parametreli sorgular (injection yok)
- SSRF: scraper yalnızca allowlist `sources` tablosundaki host’lara gider

---

## 9. Dizin Yapısı ve Modül Sorumlulukları

```
CuraNews-Aggregator/
├── IMPLEMENTATION_PLAN.md          # Bu master plan
├── README.md                       # Kurulum + demo senaryosu
├── pyproject.toml                  # Poetry ise
├── poetry.lock                     # veya
├── requirements.in / requirements.txt  # pip-tools ise
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
├── alembic/
│   └── versions/
├── docs/
│   ├── architecture.md
│   ├── scrumban-board.md
│   ├── sources.md                  # izinli kaynak listesi
│   ├── api.md
│   └── adr/
│       ├── 001-modular-monolith.md
│       ├── 002-fastapi.md
│       └── ...
├── src/
│   └── curanews/
│       ├── __init__.py
│       ├── __main__.py             # CLI giriş
│       ├── config.py
│       ├── logging_setup.py
│       ├── domain/
│       │   └── models.py           # Pydantic domain
│       ├── scrapers/
│       │   ├── base.py             # SourceAdapter
│       │   ├── static_spider.py
│       │   └── parse_bs4.py
│       ├── browser/
│       │   ├── playwright_fetcher.py
│       │   └── scroll.py
│       ├── resilience/
│       │   ├── backoff.py
│       │   └── rate_limit.py
│       ├── privacy/
│       │   └── pii.py
│       ├── ingestion/
│       │   └── pipeline.py
│       ├── db/
│       │   ├── session.py
│       │   ├── models.py           # ORM
│       │   └── repositories.py
│       ├── cache/
│       │   └── redis_client.py
│       ├── nlp/
│       │   ├── spacy_pipe.py
│       │   └── curation.py
│       └── api/
│           ├── main.py
│           ├── deps.py
│           └── routers/
│               ├── health.py
│               ├── articles.py
│               ├── feed.py
│               └── reads.py
├── web/                            # Faz 4 UI
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── scripts/
    ├── seed_demo.py
    └── run_scrape.py
```

**Bağımlılık yönü (içeri doğru):**  
`api` → `nlp/curation`, `db`, `cache`  
`ingestion` → `privacy`, `nlp`, `db`, `cache`  
`scrapers/browser` → `resilience`, `domain`  
Çevrim yok: `db` asla `api` import etmez.

---

## 10. 20 Günlük Takvim (Gün Gün)

> Takvim **rehberdir**; Scrumban pull ile sapmalar normaldir. WIP=2 bozulmaz.

| Gün | Kova | Odak görev(ler) | Gün sonu “Done görüntüsü” |
|-----|------|-----------------|---------------------------|
| 1 | B1 | G1, G2 | Repo + Scrumban panosu ayakta |
| 2 | B1 | G3 | Kilitli bağımlılıklar kuruluyor |
| 3 | B1 | G4 | Config + structured logging |
| 4 | B1 | G5 | İlk spider çıktı veriyor |
| 5 | B1 | G5 buffer + Review/Retro | Faz 1 demo |
| 6 | B2 | G6 | Playwright sayfa açıyor |
| 7 | B2 | G7 | Scroll ile ekstra item |
| 8 | B2 | G8 | Ortak adapter sözleşmesi |
| 9 | B2 | G9 | Backoff simülasyonu logda |
| 10 | B2 | G10 + Review/Retro | Polite policy + Faz 2 demo |
| 11 | B3 | G11 | Migration + CRUD |
| 12 | B3 | G12 | Redis hit/miss kanıtı |
| 13 | B3 | G13 | Dedupe pipeline |
| 14 | B3 | G14 | spaCy etiketleri DB’de |
| 15 | B3 | G15 + Review/Retro | Kürasyon farkı + PII scrub |
| 16 | B4 | G16 | OpenAPI’de uçlar |
| 17 | B4 | G17 | Gerçek feed entegrasyonu |
| 18 | B4 | G18 | UI okuma akışı |
| 19 | B4 | G19 | Testler yeşil |
| 20 | B4 | G20 + Final Review | Compose demo + teslim |

---

## 11. Fazlar ve 20 Görev (Detaylı Issue Spec)

Her görev için: **Amaç · Bağlam · Teslimatlar · Teknik yaklaşım · Bağımlılıklar · Kabul kriterleri · Doğrulama komutları (hedef) · Riskler**.

---

### Faz 1 — Foundation  
**Kova B1 · Gün 1–5 · Etiket:** `milestone:faz-1`  
**Faz hedefi:** Geliştirme ortamı, yönetim panosu ve ilk statik scraper iskeleti.  
**Faz çıkış demo’su:** Mentor panoyu görür; `scrapy crawl ...` veya CLI ile en az 3 madde JSON üretilir; bağımlılıklar kilitlidir.

#### Faz 1 ilerleme

- [x] G1 ≡ [GitHub Issue #1](https://github.com/Faruk-T/CuraNews_Aggregator/issues/1)
- [ ] G2
- [x] G3 ≡ [Issue #2](https://github.com/Faruk-T/CuraNews_Aggregator/issues/2) (dependency pinning — Poetry)
- [x] G4 (config + logging — Day 2)
- [x] G5 ≡ [Issue #4](https://github.com/Faruk-T/CuraNews_Aggregator/issues/4) (Scrapy base spider — Day 4)

---

#### [x] G1 — Repo ve proje iskeleti _(Issue #1 — Day 1)_

- **Amaç:** Yeniden üretilebilir proje iskeleti oluşturmak.
- **Bağlam:** Boş klasörden standart Python paketine geçiş; sonraki tüm işlerin zemini.
- **Teslimatlar:**
  - Git repo init
  - `.gitignore` (venv, `.env`, `__pycache__`, `.pytest_cache`, Playwright artifacts)
  - `README.md` iskeleti (kurulum yer tutucu)
  - `src/curanews/` paket iskeleti + `__main__.py` placeholder
  - Modül paketleri: `scrapers`, `browser`, `resilience`, `privacy`, `ingestion`, `db`, `cache`, `nlp`, `api`
  - `docs/`, `tests/`, `web/`, `scripts/` yer tutucuları
- **Teknik yaklaşım:** `src` layout; paket adı `curanews`.
- **Bağımlılıklar:** Yok
- **Kabul kriterleri:**
  - [x] `python -m curanews` (veya eşdeğer) çalışır ve versiyon/hello basar
  - [x] `.env` git’te yok; `.gitignore` doğrulanmış
- **Doğrulama:** `$env:PYTHONPATH="src"; python -m curanews`
- **Risk:** Windows path / encoding — UTF-8 ve PowerShell notları README’ye
- **Tamamlandı:** 2026-07-27 — branch `day-1-project-skeleton`

---

#### [ ] G2 — Scrumban panosu kurulumu

- **Amaç:** Fiziksel/dijital yönetim yüzeyini kurmak.
- **Teslimatlar:**
  - GitHub Projects / Trello / Notion board
  - Kolonlar + WIP limitleri yazılı
  - G1–G20 kartları
  - 4 Milestone
  - `docs/scrumban-board.md` (ekran görüntüsü veya link + kurallar)
- **Kabul kriterleri:**
  - [ ] Ready WIP≤5, In Progress WIP≤2 görünür şekilde not edilmiş
  - [ ] Planning trigger (Ready<3) yazılı
  - [ ] Tüm Must kartları öncelik etiketli
- **Bağımlılıklar:** G1 (repo linki için ideal)
- **Risk:** Pano süs olup kural uygulanmazsa — ilk retro’da WIP sayımı zorunlu madde

---

#### [x] G3 — Bağımlılık sabitleme (Poetry veya pip-tools) _(Issue #2 — Day 2)_

- **Amaç:** Her ortamda aynı kütüphane sürümleri.
- **Karar:** **Poetry** (`pyproject.toml` + `poetry.lock`).
- **Teslimatlar:** lock dosyası, kurulum talimatı (`docs/dependency-pinning.md`), `.env.example`
- **Kabul kriterleri:**
  - [x] Temiz ortamda `poetry install` ile kurulum
  - [x] Lock dosyası commitli
  - [x] “Dependency Pinning” bölümü README / docs’ta
- **Tamamlandı:** 2026-07-28 — branch `day-2-dependency-pinning`

---

#### [x] G4 — Yapılandırma ve logging iskeleti _(Day 2)_

- **Amaç:** `os.environ` dağınıklığını önlemek; gözlemlenebilirlik.
- **Teslimatlar:**
  - `config.py` (pydantic-settings)
  - `logging_setup.py` (key=value structured)
  - `.env.example` alanları Settings ile hizalı
- **Kabul kriterleri:**
  - [x] `LOG_LEVEL=DEBUG` ile daha fazla log
  - [x] Unit testler env override’ı doğrular
- **Bağımlılıklar:** G3
- **Tamamlandı:** 2026-07-28 — branch `day-2-dependency-pinning`

---

#### [x] G5 — Scrapy + BeautifulSoup statik spider _(Issue #4 — Day 4)_

- **Amaç:** İlk gerçek veri kazıma dikeyi.
- **Teslimatlar:**
  - Scrapy `example_news` spider + `BaseNewsSpider`
  - BS4 parse helper (`parse_bs4.py`)
  - Fixture: `tests/fixtures/example_news_listing.html`
  - `scripts/run_scrape.py` → JSONL çıktı
  - AutoThrottle + DOWNLOAD_DELAY settings
  - `docs/sources.md` / `docs/scraping.md`
- **Teknik yaklaşım:** Offline-safe HTML fixture; live URL opsiyonel `-a start_url=`.
- **Kabul kriterleri:**
  - [x] En az 3 madde: `title`, `url`, content/summary
  - [x] Çıktı JSON Lines (`data/local/scraped_news.jsonl`)
  - [x] AutoThrottle açık, DOWNLOAD_DELAY ≥ 1s
- **Bağımlılıklar:** G3, G4, Issue #3 item şeması
- **Tamamlandı:** 2026-07-30 — branch `day-4-scrapy-base-spider`
- **Faz 1 çıkış kapısı:** Bu görev Done olmadan Faz 2’ye geçilmez (Must).
---

### Faz 2 — Acquisition & Resilience  
**Kova B2 · Gün 6–10 · Etiket:** `milestone:faz-2`  
**Faz hedefi:** Dinamik içerik + anti-bot dayanıklılığı + ortak adapter.  
**Faz çıkış demo’su:** Playwright ile scroll kanıtı; backoff log eğrisi; `SourceAdapter` iki implementasyon.

#### Faz 2 ilerleme

- [ ] G6
- [ ] G7
- [ ] G8
- [ ] G9
- [ ] G10

---

#### [ ] G6 — Playwright async altyapısı

- **Amaç:** Browser lifecycle’ı güvenli yönetmek.
- **Teslimatlar:** `browser/playwright_fetcher.py` — launch, context, close, timeout
- **Kabul kriterleri:**
  - [ ] Headless sayfa açma
  - [ ] Exception’da browser sızıntısı yok (`try/finally` veya async context manager)
- **Risk:** İlk kurulumda `playwright install` unutulması — README adımı zorunlu

---

#### [ ] G7 — Infinite scroll / dinamik içerik stratejisi

- **Amaç:** JS ile sonradan yüklenen öğeleri toplamak.
- **Teslimatlar:** `scroll.py` — max scroll, stable-height stop, item selector
- **Kabul kriterleri:**
  - [ ] Scroll öncesi/sonrası item sayısı ölçülür; **N ≥ 1** artış dokümante
  - [ ] ToS engelinde fixture sayfası ile aynı desen kanıtlanır (ADR-003)
- **Bağımlılıklar:** G6

---

#### [ ] G8 — SourceAdapter birleştirme

- **Amaç:** Scrapy ve Playwright çıktısını tek tipe indirgemek.
- **Teslimatlar:** `SourceAdapter` Protocol + `StaticSourceAdapter` + `DynamicSourceAdapter` + ortak `RawArticle`
- **Kabul kriterleri:**
  - [ ] Aynı consumer fonksiyonu her iki adaptör listesini işler
  - [ ] Unit test: fake adapter
- **Bağımlılıklar:** G5, G6

---

#### [ ] G9 — Exponential backoff & rate limiting

- **Amaç:** Ban/yıkım riskini ve gereksiz yükü azaltmak.
- **Teslimatlar:** `resilience/backoff.py`, kaynak cooldown (bellek veya Redis hazır arayüz)
- **Kabul kriterleri:**
  - [ ] Simüle 429’da delay’ler loglanır (artarak)
  - [ ] `max_retries` sonrası kontrollü fail
  - [ ] Sınırsız while-retry yok
- **Formül:** §6.4

---

#### [ ] G10 — Polite crawling & güvenlik sınırları

- **Amaç:** Etik/operasyonel politikayı kod + dokümana gömmek.
- **Teslimatlar:**
  - allowlist
  - UA politikası
  - concurrency config
  - `docs/sources.md` + etik bölüm README
- **Kabul kriterleri:**
  - [ ] Allowlist dışı host reddedilir
  - [ ] Varsayılan concurrency ≤ 2
- **Faz 2 çıkış kapısı:** G8 + G9 Must; G7 Should (fixture ile kapanabilir).

---

### Faz 3 — Store, Cache, NLP, Curation  
**Kova B3 · Gün 11–15 · Etiket:** `milestone:faz-3`  
**Faz hedefi:** Kalıcı veri + cache + zeka + gizlilik.  
**Faz çıkış demo’su:** Aynı haberi iki kez kazıyınca tek satır; iki kullanıcıda farklı sıralama; PII maskeli örnek.

#### Faz 3 ilerleme

- [ ] G11
- [ ] G12
- [ ] G13
- [ ] G14
- [ ] G15

---

#### [ ] G11 — PostgreSQL şeması ve migrasyonlar

- **Amaç:** Source of truth’u kurmak.
- **Teslimatlar:** Docker’da Postgres, SQLAlchemy modelleri, Alembic migration, seed script iskeleti
- **Kabul kriterleri:**
  - [ ] `alembic upgrade head` temiz uygulanır
  - [ ] CRUD smoke (article insert/select)
- **Şema:** §7.2

---

#### [ ] G12 — Redis önbellekleme katmanı

- **Amaç:** Tekrarlı pahalı işleri ve scrape fırtınasını kesmek.
- **Teslimatlar:** Redis client wrapper, feed cache get/set, scrape lock/cooldown helper
- **Kabul kriterleri:**
  - [ ] Aynı feed isteğinde `HIT` log/metric
  - [ ] TTL sonrası `MISS`
- **Degrade:** Redis yokken API ayakta kalsın (best-effort)

---

#### [ ] G13 — Ingestion pipeline

- **Amaç:** Adapter → DB üretim hattı.
- **Akış:** normalize → canonical URL → hashes → privacy scrub → upsert → (nlp çağrısı G14 ile bağlanır)
- **Kabul kriterleri:**
  - [ ] Aynı `url_hash` ikinci kez gelince yeni satır yok (update veya no-op)
  - [ ] Pipeline birim testi fixture ile yeşil
- **Bağımlılıklar:** G8, G11

---

#### [ ] G14 — spaCy NLP entity/topic

- **Amaç:** Haberleri aranabilir/kürasyonlanabilir kılmak.
- **Teslimatlar:** model indirme dokümanı, `spacy_pipe.py`, `article_entities` yazımı
- **Kabul kriterleri:**
  - [ ] Örnek metinde en az 1 entity türü beklenen şekilde çıkar
  - [ ] Model yoksa anlamlı hata + degrade stratejisi dokümante
- **Not:** TR model yoksa EN model + TR için kuralsal topic keyword listesi geçici kabul

---

#### [ ] G15 — Algoritmik kürasyon + PII pseudonymization

- **Amaç:** Ürünün “akıl” ve “sorumluluk” katmanı.
- **Teslimatlar:**
  - `curation.py` skor formülü (§7.5)
  - `privacy/pii.py` email/phone/handle scrub
  - iki demo kullanıcı seed’i
- **Kabul kriterleri:**
  - [ ] User A vs B sıralaması farklı (ekran görüntüsü veya test assert)
  - [ ] Fixture metinde e-posta/handle maskeli
- **Faz 3 çıkış kapısı:** G11, G13, G15 Must; G12/G14 Should ama güçlü önerilir.

---

### Faz 4 — API, UI, Test, Deploy  
**Kova B4 · Gün 16–20 · Etiket:** `milestone:faz-4`  
**Faz hedefi:** Ürünleştirme ve teslim.  
**Faz çıkış demo’su:** Tarayıcıdan feed; okundu sonrası sıralama kayması; Compose ile 3. kişi kurulumu.

#### Faz 4 ilerleme

- [ ] G16
- [ ] G17
- [ ] G18
- [ ] G19
- [ ] G20

---

#### [ ] G16 — FastAPI REST iskeleti

- **Amaç:** HTTP yüzeyi.
- **Teslimatlar:** router’lar (§7.6), Pydantic response modelleri, `/docs`
- **Kabul kriterleri:**
  - [ ] `/health` 200
  - [ ] OpenAPI’de articles/feed/reads görünür (stub olsa bile)

---

#### [ ] G17 — API ↔ DB / Redis / NLP entegrasyonu

- **Amaç:** Stub’ları gerçek veriye bağlamak.
- **Kabul kriterleri:**
  - [ ] `/feed` gerçek tablolardan scorlu liste döner
  - [ ] Cache header veya body alanında `hit|miss`
  - [ ] `POST /reads` sonrası (cache invalidate) sıralama değişebilir
- **Bağımlılıklar:** G12, G15, G16

---

#### [ ] G18 — Web arayüzü

- **Amaç:** Mentorsuz tıklanabilir demo.
- **Kapsam (bilinçli sade):**
  - Haber listesi / feed
  - Konu filtresi (basit)
  - Okundu butonu
  - Mobilde kırılmayan tek sütun layout
- **Kabul kriterleri:**
  - [ ] Desktop + dar ekranda akış tamam
  - [ ] API down ise anlaşılır hata mesajı
- **Tasarım notu:** Mevcut bir design system yok; sade, okunaklı, kart yağmuruna boğmayan arayüz. Marka adı “CuraNews” ilk bakışta görünür olsun.

---

#### [x] G19 — Entegrasyon testleri

- **Amaç:** Regresyon ağı.
- **Teslimatlar:**
  - pytest
  - API integration (TestClient)
  - curation unit test (A≠B sıralama)
  - dedupe test
  - mümkünse Redis fake/fakeredis veya skip marker
- **Kabul kriterleri:**
  - [x] `pytest` tek komutla yeşil
  - [x] CI yoksa bile script/README’de komut var

---

#### [ ] G20 — Dağıtım ve staj teslim paketi

- **Amaç:** Başkasının çalıştırabilmesi.
- **Teslimatlar:**
  - `docker-compose.yml` (api + db + redis)
  - güncel README (5 adımlı quickstart)
  - demo senaryosu (aşağıda §13)
  - mimari özeti (`docs/architecture.md`)
  - bu planın checkbox’ları güncel
- **Kabul kriterleri:**
  - [ ] Temiz makinede Compose ile feed görünür (veya video + mentor onayı)
  - [ ] Secret örneği dışında gerçek secret yok
- **Final çıkış kapısı:** Must’lar kapalı; demo tekrarlanabilir.

---

## 12. Test, Kalite ve CI Stratejisi

### 12.1 Test Piramidi (staj ölçeği)

| Katman | Örnek | Araç |
|--------|-------|------|
| Unit | backoff delay, PII mask, score(A)≠score(B) | pytest |
| Integration | ingestion dedupe, `/feed` | pytest + TestClient + test DB |
| Smoke / E2E (ince) | compose up + curl health | script |

### 12.2 Minimum Zorunlu Testler (G19)

1. `test_backoff_increases`
2. `test_pii_masks_email`
3. `test_dedupe_same_url`
4. `test_curation_orders_differ_for_two_users`
5. `test_health_ok`
6. `test_feed_shape`

### 12.3 Kalite kapıları

- Format: ruff/black (seçim G3’te)
- Type: mypy opsiyonel (Could)
- Pre-commit opsiyonel; zorunlu değil

---

## 13. Dağıtım, Demo ve Teslim Paketi

### 13.1 Hedef çalışma topolojisi

```
docker compose:
  - db (Postgres)
  - redis
  - api (uvicorn curanews.api.main:app)
  - (opsiyonel) worker scrape
web/ → API’ye tarayıcıdan veya api’nin static mount’u
```

### 13.2 Mentor Demo Senaryosu (10 dakika)

1. Pano: Scrumban kolonları + WIP anlatımı (1 dk)
2. `docker compose up --build` (veya hazır stack) (2 dk)
3. `/docs` → `/health` (1 dk)
4. Scrape tetikle veya seed göster (2 dk)
5. UI’da User A feed vs User B feed farkı (2 dk)
6. PII fixture öncesi/sonrası (1 dk)
7. Riskler ve etik sınırlar (1 dk)

### 13.3 Teslim Kontrol Listesi

- [ ] README quickstart
- [ ] `.env.example`
- [ ] Lock dosyası
- [ ] `docs/architecture.md`
- [ ] `docs/sources.md`
- [ ] Testler yeşil
- [ ] IMPLEMENTATION_PLAN checkbox’ları güncel
- [ ] Kısa staj raporu / sunum notları (opsiyonel ama önerilir)

---

## 14. Risk Kaydı, MoSCoW ve Escalation

### 14.1 Risk Kaydı

| ID | Risk | Olasılık | Etki | Azaltma | Sahip |
|----|------|----------|------|---------|-------|
| R1 | Sosyal ToS / bot engeli | Y | Y | Fixture + ADR-003; Must’u dinamik haber sitesine kaydır | Stajyer |
| R2 | Kapsam şişmesi | Y | Y | WIP=2, MoSCoW, Won’t listesi | Stajyer+Mentor |
| R3 | spaCy kurulum/model | O | O | `sm` model; degrade | Stajyer |
| R4 | Windows/Docker sürtünmesi | O | O | Erken G11’de Compose dene | Stajyer |
| R5 | Secret sızıntısı | D | Y | gitignore, örnek env, review | Stajyer |
| R6 | Kaynak HTML değişimi | Y | O | Fixture + adaptör testleri | Stajyer |
| R7 | Redis zorunlu sanılması | O | O | Degrade path | Stajyer |

### 14.2 MoSCoW

| Seviye | Görevler |
|--------|----------|
| **Must** | G1, G2, G3, G4, G5, G8, G9, G11, G13, G15, G16, G17, G20 |
| **Should** | G6, G7, G10, G12, G14, G18, G19 |
| **Could** | Gelişmiş UI, mypy strict, CI badge, çoklu dil |
| **Won’t** | Native mobile, K8s, login-bypass, real-time at scale |

> Should’lar zaman kalmazsa bilinçli olarak sonraki kovaya taşınır; Must’lar bitmeden Could’a geçilmez.

### 14.3 Escalation

1. Blocked > 4 saat → Daily’de mentor’a görünür et.
2. Must görev gün aşımı → kapsam kes (Could/Should), Won’t’a yaz.
3. Yasal/etik şüphe → kazımayı durdur, fixture’a geç, kararı dokümante et.

---

## 15. Sözlük (Glossary)

| Terim | Anlam |
|-------|-------|
| **Scrumban** | Scrum ritmi + Kanban akış/WIP/pull hibriti |
| **WIP** | Work in Progress — eşzamanlı aktif iş sayısı limiti |
| **Pull** | Kapasite açılınca işi Ready’den çekme; atama ile itmeme |
| **Bucket size planning** | İşin vizyon→gereksinim→görev kovalarından süzülmesi |
| **On-demand planning** | Ready eşiği altınca yapılan kısa planlama |
| **DoR / DoD** | Ready/Done tanımları |
| **Adapter** | Kaynak tipini ortak `RawArticle` arayüzüne çeviren bileşen |
| **Ingestion** | Ham maddenin temizlenip DB’ye yazılması |
| **Dedupe** | Tekrar haberlerin tek kayda indirgenmesi |
| **NER** | Named Entity Recognition — kişi/kurum/yer çıkarımı |
| **Algorithmic Curation** | Okuma geçmişine dayalı skorlu sıralama/filtreleme |
| **Pseudonymization** | Kimliği geri dönüşü kontrollü şekilde gizleme (hash+salt) |
| **Exponential backoff** | Hata sonrası üstel artan bekleme ile retry |
| **Dependency pinning** | Kütüphane sürümlerini kilitleme |
| **Source of truth** | Kalıcı doğruluk kaynağı (bu projede PostgreSQL) |
| **ADR** | Architecture Decision Record |

---

## 16. İlerleme Panosu

### 16.1 Faz özeti

| Faz | Görevler | Durum | Review tarihi |
|-----|----------|-------|---------------|
| Faz 1 | G1–G5 | [x] Faz 1 kazıma dikeyi + SQLite pipeline (Issue #5) — review/retro | Gün 5 |
| Faz 2 | G6–G10 | [~] Issue #6 Playwright (Day 6) — Issue #7 sırada | Gün 10 |
| Faz 3 | G11–G15 | [ ] Başlanmadı | Gün 15 |
| Faz 4 | G16–G20 | [ ] Başlanmadı | Gün 20 |

### 16.2 Görev özeti

| ID | GitHub Issue | Başlık | MoSCoW | Faz | Durum |
|----|--------------|--------|--------|-----|-------|
| G1 | [#1](https://github.com/Faruk-T/CuraNews_Aggregator/issues/1) | Repo iskeleti | Must | 1 | [x] |
| G2 | (pano) | Scrumban panosu | Must | 1 | [ ] |
| G3 | [#2](https://github.com/Faruk-T/CuraNews_Aggregator/issues/2) | Dependency pinning | Must | 1 | [x] |
| G4 | — | Config + logging | Must | 1 | [x] |
| G5 | [#4](https://github.com/Faruk-T/CuraNews_Aggregator/issues/4) | Scrapy/BS4 spider | Must | 1 | [x] |
| — | [#5](https://github.com/Faruk-T/CuraNews_Aggregator/issues/5) | SQLite pipeline + dedupe | Must | 1 | [x] (Day 5, commit pending) |
| G6 | [#6](https://github.com/Faruk-T/CuraNews_Aggregator/issues/6) | Playwright altyapı | Should | 2 | [x] (Day 6, commit pending) |
| G7 | [#6](https://github.com/Faruk-T/CuraNews_Aggregator/issues/6) | Infinite scroll | Should | 2 | [ ] |
| G8 | [#8](https://github.com/Faruk-T/CuraNews_Aggregator/issues/8)/adapter | SourceAdapter | Must | 2 | [ ] |
| G9 | [#7](https://github.com/Faruk-T/CuraNews_Aggregator/issues/7) | Exp. backoff | Must | 2 | [ ] |
| G10 | [#10](https://github.com/Faruk-T/CuraNews_Aggregator/issues/10) | Polite crawling / clean pipeline | Should | 2 | [ ] |
| G11 | [#11](https://github.com/Faruk-T/CuraNews_Aggregator/issues/11) | PostgreSQL schema | Must | 3 | [ ] |
| G12 | [#12](https://github.com/Faruk-T/CuraNews_Aggregator/issues/12) | Redis cache | Should | 3 | [ ] |
| G13 | [#5](https://github.com/Faruk-T/CuraNews_Aggregator/issues/5)/#13 | Ingestion/dedupe | Must | 3 | [ ] |
| G14 | [#14](https://github.com/Faruk-T/CuraNews_Aggregator/issues/14) | spaCy NLP | Should | 3 | [ ] |
| G15 | [#13](https://github.com/Faruk-T/CuraNews_Aggregator/issues/13)/[#15](https://github.com/Faruk-T/CuraNews_Aggregator/issues/15) | Curation + PII | Must | 3 | [ ] |
| G16 | [#16](https://github.com/Faruk-T/CuraNews_Aggregator/issues/16) | FastAPI iskelet | Must | 4 | [ ] |
| G17 | [#17](https://github.com/Faruk-T/CuraNews_Aggregator/issues/17) | API entegrasyon / pagination | Must | 4 | [ ] |
| G18 | [#18](https://github.com/Faruk-T/CuraNews_Aggregator/issues/18) | Web UI | Should | 4 | [ ] |
| G19 | [#19](https://github.com/Faruk-T/CuraNews_Aggregator/issues/19) | Frontend integration | Should | 4 | [x] |
| G20 | [#20](https://github.com/Faruk-T/CuraNews_Aggregator/issues/20) | Deploy + teslim | Must | 4 | [ ] |

**Genel ilerleme:** **6 izlenen iş** (G1,G3,G4,G5 + Issue #3 + Issue #5) · Faz 1 dikeyi SQLite’a kadar tamam

---

## 17. Sonraki Adım

1. Bu master planı mentor ile **15 dakikada gözden geçir** (özellikle ADR-003 sosyal medya sınırı ve FastAPI kararı).
2. Scrumban panosunu aç (G2) ve G1+G3’ü Ready’ye al.
3. WIP=2 kuralı ile **G1’i In Progress’e çek** ve kodlamaya başla.
4. Her Done’da bu dosyadaki ilgili kutuyu `[x]` yap.

---

### Belge geçmişi

| Sürüm | Tarih | Not |
|-------|-------|-----|
| 1.0 | 2026-07-27 | İlk plan iskeleti |
| 2.0 | 2026-07-27 | Master plan: Scrumban derinliği, ADR, ER, API, skor, gün gün takvim, issue spec’ler |
| 2.1 | 2026-07-27 | G1 / Issue #1 tamam; GitHub issue eşlemesi eklendi |
| 2.2 | 2026-07-28 | G3/G4 / Issue #2: Poetry pinning + Settings/logging |
| 2.4 | 2026-07-30 | G5 / Issue #4: Scrapy example_news spider, AutoThrottle, BS4 parser |
| 2.5 | 2026-07-31 | Issue #5: clean->validate->dedupe->SQLite pipelines |
| 2.6 | 2026-08-04 | Issue #6: Playwright async + infinite scroll fixture |

---

*CuraNews-Aggregator — Scrumban + Bucket Planning · Master Implementation Plan v2.6*  
*Bu belge projenin tek uçtan uca referansıdır; çelişen kısa notlar varsa önce bu dosya güncellenir.*