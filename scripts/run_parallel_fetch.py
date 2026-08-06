"""Run parallel multi-source fetch demo (Issue #9).

Usage::

    poetry run python scripts/run_parallel_fetch.py
    poetry run python scripts/run_parallel_fetch.py --adapters static,api --concurrency 2
    poetry run python scripts/run_parallel_fetch.py --browser-demo
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from curanews.browser.concurrent import fetch_urls_concurrent
from curanews.browser.dynamic_listing import fixture_file_url
from curanews.config import get_settings
from curanews.scrapers.adapters import get_adapter
from curanews.scrapers.adapters._paths import fixture_path
from curanews.scrapers.parallel import ingest_adapters_parallel_sync


def _parse_adapters(raw: str) -> list[str]:
    names = [part.strip() for part in raw.split(",") if part.strip()]
    return names or ["static", "api"]


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Parallel asyncio fetch demo (Issue #9)")
    parser.add_argument(
        "--adapters",
        default="static,api",
        help="Comma-separated adapter names (default: static,api)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=settings.scrape_concurrency,
        help="Max concurrent workers (default: SCRAPE_CONCURRENCY)",
    )
    parser.add_argument("--limit", type=int, default=10, help="Per-adapter article limit")
    parser.add_argument(
        "--output",
        default="data/local/parallel_news.jsonl",
        help="JSONL path for promoted articles",
    )
    parser.add_argument(
        "--browser-demo",
        action="store_true",
        help="Also run concurrent Playwright tabs on local fixtures",
    )
    args = parser.parse_args(argv)

    adapters = [get_adapter(name) for name in _parse_adapters(args.adapters)]
    summary = ingest_adapters_parallel_sync(
        adapters,
        limit=max(1, args.limit),
        concurrency=max(1, args.concurrency),
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with out_path.open("w", encoding="utf-8") as handle:
        for result in summary.results:
            for article in result.articles:
                handle.write(article.model_dump_json() + "\n")
                written += 1

    payload: dict = {
        "mode": "adapters",
        "concurrency": summary.concurrency,
        "wall_seconds": round(summary.wall_seconds, 4),
        "sequential_estimate_seconds": round(summary.sequential_estimate_seconds, 4),
        "ok_adapters": summary.ok_count,
        "articles_written": written,
        "output": str(out_path),
        "per_adapter": [
            {
                "source_id": r.source_id,
                "kind": r.kind,
                "articles": len(r.articles),
                "elapsed_seconds": round(r.elapsed_seconds, 4),
                "error": r.error,
            }
            for r in summary.results
        ],
    }

    if args.browser_demo:
        static_html = fixture_path("tests", "fixtures", "example_news_listing.html")
        urls = [
            static_html.resolve().as_uri(),
            fixture_file_url(),
        ]
        browser_summary = asyncio.run(
            fetch_urls_concurrent(urls, concurrency=max(1, args.concurrency))
        )
        payload["browser_demo"] = {
            "concurrency": browser_summary.concurrency,
            "wall_seconds": round(browser_summary.wall_seconds, 4),
            "sequential_estimate_seconds": round(
                browser_summary.sequential_estimate_seconds, 4
            ),
            "ok_pages": browser_summary.ok_count,
            "pages": [
                {
                    "url": r.url,
                    "ok": r.ok,
                    "elapsed_seconds": round(r.elapsed_seconds, 4),
                    "error": r.error,
                    "html_chars": len(r.html or ""),
                }
                for r in browser_summary.results
            ],
        }

    print(json.dumps(payload, indent=2))
    return 0 if written else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
