# Allowed sources

Document each crawl target here before enabling it in code.

| Source key | Kind | Base URL | robots respected | Notes | Enabled |
|------------|------|----------|------------------|-------|---------|
| `example_news` | static | fixture `tests/fixtures/example_news_listing.html` | n/a (local file) | Day 4 demo spider; offline-safe | yes (demo) |
| `dynamic_demo` | dynamic | fixture `tests/fixtures/dynamic_news_scroll.html` | n/a (local file) | Day 6 Playwright infinite-scroll demo | yes (demo) |

## Policy

- Public / permitted content only.
- No login wall or CAPTCHA bypass.
- Default concurrency ≤ 2.
- User-Agent: `CuraNewsBot/0.1 (+https://github.com/Faruk-T/CuraNews_Aggregator)`
- Prefer fixture/demo markup before hitting live sites during internship demos.
