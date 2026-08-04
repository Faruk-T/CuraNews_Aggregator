"""Run the Day 6 Playwright infinite-scroll demo against the local fixture.

Usage::

    poetry run playwright install chromium
    poetry run python scripts/run_playwright_scrape.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from curanews.browser import fetch_dynamic_listing, fixture_file_url


async def _run(min_items: int, output: Path) -> int:
    url = fixture_file_url()
    entries, scroll = await fetch_dynamic_listing(
        url,
        source="dynamic_demo",
        base_url="https://example.com/",
        min_items=min_items,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(
                json.dumps(
                    {
                        "title": entry.title,
                        "url": entry.url,
                        "summary": entry.summary,
                        "category": entry.category,
                        "published_date": entry.published_date.isoformat(),
                        "source": entry.source,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(f"scroll_initial={scroll.initial_count} scroll_final={scroll.final_count}")
    print(f"scroll_rounds={scroll.rounds} parsed_entries={len(entries)}")
    print(f"output={output}")
    if entries:
        print(f"sample_title={entries[0].title!r}")
    # Issue #6 acceptance: scrolling must reveal more than the initial batch.
    if scroll.final_count <= scroll.initial_count:
        print("Scroll did not increase item count", file=sys.stderr)
        return 1
    if len(entries) < min_items:
        print(f"Expected at least {min_items} entries, got {len(entries)}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Playwright dynamic listing demo")
    parser.add_argument("--min-items", type=int, default=4)
    parser.add_argument(
        "--output",
        default="data/local/playwright_news.jsonl",
    )
    args = parser.parse_args(argv)
    return asyncio.run(_run(args.min_items, Path(args.output)))


if __name__ == "__main__":
    raise SystemExit(main())
