# Allowed sources (Issue #10 / G10; RSS catalog G19)

Document each crawl target here **before** enabling it in code or `.env`.

CuraNews is an **aggregator**: it does not invent articles. Headlines come from
publisher syndication feeds (RSS/Atom) or, optionally, a GNews-compatible JSON API.
HTML scraping of arbitrary news sites is not the production path.

| Source key | Kind | Base URL / host | robots / ToS | Notes | Enabled |
|------------|------|-----------------|--------------|-------|---------|
| `rss_catalog` | rss | see catalog below | official RSS | **Default live path** — no API key | yes |
| `gnews_api` | api | `gnews.io` | provider ToS | Live only if `NEWS_API_KEY` is set; else fixture | optional |
| `example_news` | static | `example.com` (fixture file) | n/a (local file) | Day 4 spider / unit tests | demo only |
| `dynamic_demo` | dynamic | `file://` scroll fixture | n/a (local file) | Day 6 Playwright demo | demo only |

## RSS catalog (production news)

Defined in `src/curanews/scrapers/adapters/rss_catalog.py`:

| Feed key | Publisher | Feed URL |
|----------|-----------|----------|
| `bbc_world` | BBC News | `https://feeds.bbci.co.uk/news/world/rss.xml` |
| `bbc_turkish` | BBC Türkçe | `https://feeds.bbci.co.uk/turkce/rss.xml` |
| `guardian_world` | The Guardian | `https://www.theguardian.com/world/rss` |
| `npr_news` | NPR | `https://feeds.npr.org/1001/rss.xml` |
| `aljazeera_english` | Al Jazeera | `https://www.aljazeera.com/xml/rss/all.xml` |
| `aa_guncel` | Anadolu Ajansı | `https://www.aa.com.tr/tr/rss/default?cat=guncel` |
| `dw_turkish` | DW Türkçe | `https://rss.dw.com/xml/rss-tur-all` |
| `trt_haber` | TRT Haber | `https://www.trthaber.com/sondakika.rss` |
| `ahaber_home` | A Haber | `https://www.ahaber.com.tr/rss/anasayfa.xml` |
| `ahaber_spor` | A Haber Spor | `https://www.ahaber.com.tr/rss/spor.xml` |
| `ntv_gundem` | NTV | `https://www.ntv.com.tr/gundem.rss` |
| `ntv_spor` | NTV Spor | `https://www.ntv.com.tr/sporskor.rss` |
| `cnnturk_spor` | CNN Türk Spor | `https://www.cnnturk.com/feed/rss/spor/news` |
| `hurriyet_spor` | Hürriyet Spor | `https://www.hurriyet.com.tr/rss/spor` |
| `milliyet_spor` | Milliyet Spor | `https://www.milliyet.com.tr/rss/rssNew/sporRss.xml` |
| `haberturk` | Habertürk | `https://www.haberturk.com/rss` |

TRT Spor (`trtspor.com.tr`) public RSS yayınlamıyor; spor masası NTV Spor, A Haber Spor, Hürriyet/Milliyet/CNN Türk Spor ve TRT Haber ile doldurulur.

These are **publisher-provided syndication endpoints**. CuraNews stores title, summary,
canonical URL and metadata, then links the reader to the original article. Full
paywalled HTML is not scraped.

Refresh the database:

```powershell
docker compose up -d postgres redis
poetry run alembic upgrade head
poetry run python scripts/refresh_news.py
poetry run python scripts/smoke_rss.py   # optional: ping each catalog feed
```

## Allowlist env

```env
SCRAPE_ALLOWLIST_HOSTS=example.com,gnews.io,localhost,127.0.0.1,feeds.bbci.co.uk,www.theguardian.com,feeds.npr.org,www.aljazeera.com,rss.dw.com,www.aa.com.tr,www.trthaber.com,www.ahaber.com.tr,www.ntv.com.tr,www.cnnturk.com,www.hurriyet.com.tr,www.milliyet.com.tr,www.haberturk.com
```

If your local `.env` was copied before this list, update `SCRAPE_ALLOWLIST_HOSTS`
or RSS fetches will fail closed (`HostNotAllowedError`).

Add a host only after legal/ToS review and mentor sign-off.

## Policy checklist

- Public / permitted content only
- Prefer official RSS over HTML scraping
- No login wall or CAPTCHA bypass
- Default concurrency ≤ 2 (`SCRAPE_CONCURRENCY`)
- Identifying User-Agent (`SCRAPE_USER_AGENT`)
- Prefer fixtures in unit tests; live RSS is opt-in (`CURANEWS_LIVE_RSS=1`)
- HTML noise stripped before `NewsArticle` promotion (`clean_raw_draft`)
