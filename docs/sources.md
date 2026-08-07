# Allowed sources (Issue #10 / G10)

Document each crawl target here **before** enabling it in code or `.env`.

| Source key | Kind | Base URL / host | robots respected | Notes | Enabled |
|------------|------|-----------------|------------------|-------|---------|
| `example_news` | static | `example.com` (fixture file) | n/a (local file) | Day 4 demo spider | yes (demo) |
| `dynamic_demo` | dynamic | `file://` scroll fixture | n/a (local file) | Day 6 Playwright demo | yes (demo) |
| `gnews_api` | api | `gnews.io` | provider ToS | Offline JSON if no API key | yes (demo) |

## Allowlist env

```env
SCRAPE_ALLOWLIST_HOSTS=example.com,gnews.io,localhost,127.0.0.1
```

Add a host only after legal/ToS review and mentor sign-off.

## Policy checklist

- Public / permitted content only
- No login wall or CAPTCHA bypass
- Default concurrency ≤ 2 (`SCRAPE_CONCURRENCY`)
- Identifying User-Agent (`SCRAPE_USER_AGENT`)
- Prefer fixtures before live sites during internship demos
- HTML noise stripped before `NewsArticle` promotion (`clean_raw_draft`)
