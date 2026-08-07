# Day 10 evidence (Issue #10 / G10)

Take **screenshots of the IDE showing these code blocks** (not only terminal). Save under `docs/evidence/day-10/`.

| File | Screenshot name | What to capture |
|------|-----------------|-----------------|
| `src/curanews/scrapers/policy.py` | `code-allowlist-assert.png` | `assert_url_allowed()` + `HostNotAllowedError` block |
| `src/curanews/ingestion/cleaning.py` | `code-strip-html.png` | `strip_html_tags()` and `clean_raw_draft()` |
| `src/curanews/config.py` | `code-concurrency-default.png` | `scrape_concurrency` default `2` and allowlist fields |
| `src/curanews/scrapers/adapters/consumer.py` | `code-clean-before-promote.png` | `promote_draft(clean_raw_draft(draft))` line |

## Terminal checks (optional extra SS)

```powershell
poetry run pytest tests/unit/test_policy.py tests/unit/test_cleaning.py -q
poetry run python scripts/verify_crawl_policy.py
```

Expected: unknown host check fails with allowlist message; default concurrency `2`.

## Staj defteri

Reference the four code screenshots by filename when explaining allowlist, cleaning, and polite defaults.
