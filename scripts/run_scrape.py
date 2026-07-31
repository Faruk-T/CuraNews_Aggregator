"""Run the example Scrapy spider, export JSONL, and persist to SQLite.

Usage (from repo root)::

    poetry run python scripts/run_scrape.py
    poetry run python scripts/run_scrape.py --sqlite data/local/demo.sqlite3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from curanews.db import SqliteArticleStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run CuraNews example_news spider")
    parser.add_argument(
        "--start-url",
        default=None,
        help="Optional listing URL (defaults to bundled HTML fixture)",
    )
    parser.add_argument(
        "--output",
        default="data/local/scraped_news.jsonl",
        help="JSON Lines output path",
    )
    parser.add_argument(
        "--sqlite",
        default="data/local/curanews.sqlite3",
        help="SQLite database path for pipeline persistence",
    )
    args = parser.parse_args(argv)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sqlite_path = Path(args.sqlite)
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    settings = get_project_settings()
    settings.set(
        "FEEDS",
        {
            str(out_path): {
                "format": "jsonlines",
                "encoding": "utf-8",
                "overwrite": True,
                "store_empty": False,
            }
        },
        priority="cmdline",
    )
    settings.set("ROBOTSTXT_OBEY", False, priority="cmdline")
    settings.set("SQLITE_PATH", str(sqlite_path), priority="cmdline")

    process = CrawlerProcess(settings)
    crawl_kwargs = {}
    if args.start_url:
        crawl_kwargs["start_url"] = args.start_url
    process.crawl("example_news", **crawl_kwargs)
    process.start()

    if not out_path.is_file():
        print("No output file produced", file=sys.stderr)
        return 1

    lines = [ln for ln in out_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    print(f"scraped_items={len(lines)} output={out_path}")
    if lines:
        sample = json.loads(lines[0])
        print(f"sample_title={sample.get('title')!r}")

    store = SqliteArticleStore(sqlite_path)
    try:
        print(f"sqlite_rows={store.count()} sqlite_path={sqlite_path}")
        recent = store.list_recent(limit=3)
        for row in recent:
            print(f"db_title={row.title!r} category={row.category}")
    finally:
        store.close()

    return 0 if lines else 1


if __name__ == "__main__":
    raise SystemExit(main())
