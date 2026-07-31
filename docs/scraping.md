# Scraping notes (Day 4 / Issue #4)

## First spider

| Spider | Name | Purpose |
|--------|------|---------|
| `ExampleNewsSpider` | `example_news` | Static listing demo (fixture by default) |

### Run

```powershell
poetry run python scripts/run_scrape.py
# or
poetry run scrapy crawl example_news -s ROBOTSTXT_OBEY=False
```

Output: `data/local/scraped_news.jsonl` (gitignored) and SQLite rows via Issue #5 pipelines
(`data/local/curanews.sqlite3`). See [`pipeline.md`](./pipeline.md).

### Polite settings

- `DOWNLOAD_DELAY = 1.0`
- `AUTOTHROTTLE_ENABLED = True`
- `CONCURRENT_REQUESTS = 2`
- `ROBOTSTXT_OBEY = True` (disabled only for local `file://` demos in the helper script)

### Parser

`curanews.scrapers.parse_bs4.parse_example_listing` expects `article.news-card` cards with
`a.news-title` and optional `.news-summary` / `data-category` / `data-published`.

Live sites with different markup need a dedicated parser + spider (later issues).
