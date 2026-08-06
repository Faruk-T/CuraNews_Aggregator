"""Fetch articles via SourceAdapter registry (Issue #8).

Usage::

    poetry run python scripts/fetch_sources.py --list
    poetry run python scripts/fetch_sources.py --adapter static --promote
    poetry run python scripts/fetch_sources.py --adapter api --limit 5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from curanews.scrapers.adapters import adapter_label, get_adapter, ingest_from_adapter, list_adapters


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch news via unified source adapters")
    parser.add_argument("--adapter", default="api", help="Adapter name (see --list)")
    parser.add_argument("--limit", type=int, default=10, help="Max articles to fetch")
    parser.add_argument(
        "--output",
        default="data/local/api_news.jsonl",
        help="JSON Lines output path",
    )
    parser.add_argument("--list", action="store_true", help="List registered adapters")
    parser.add_argument(
        "--promote",
        action="store_true",
        help="Validate drafts to NewsArticle JSON",
    )
    args = parser.parse_args(argv)

    if args.list:
        for name in list_adapters():
            adapter = get_adapter(name)
            print(f"{name}\t{adapter_label(adapter)}")
        return 0

    adapter = get_adapter(args.adapter)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.promote:
        articles = ingest_from_adapter(adapter, limit=max(1, args.limit))
        with out_path.open("w", encoding="utf-8") as handle:
            for article in articles:
                handle.write(article.model_dump_json() + "\n")
        written = len(articles)
        fetched = written
    else:
        drafts = adapter.fetch(limit=max(1, args.limit))
        with out_path.open("w", encoding="utf-8") as handle:
            for draft in drafts:
                handle.write(draft.model_dump_json() + "\n")
        written = len(drafts)
        fetched = written

    print(
        json.dumps(
            {
                "adapter": adapter_label(adapter),
                "fetched": fetched,
                "written": written,
                "output": str(out_path),
            },
            indent=2,
        )
    )
    return 0 if written else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
