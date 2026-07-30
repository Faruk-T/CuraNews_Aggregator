"""Run the Day 4 example Scrapy spider and print item counts.

Usage (from repo root)::

    poetry run python scripts/run_scrape.py
    poetry run python scripts/run_scrape.py --start-url file:///...
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


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
    args = parser.parse_args(argv)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

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
    # Local fixture demos should not wait on robots.txt for file://
    settings.set("ROBOTSTXT_OBEY", False, priority="cmdline")

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
    return 0 if lines else 1


if __name__ == "__main__":
    raise SystemExit(main())
