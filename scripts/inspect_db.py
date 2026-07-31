"""Inspect the SQLite article store produced by Scrapy pipelines.

Usage::

    poetry run python scripts/inspect_db.py
    poetry run python scripts/inspect_db.py --sqlite data/local/curanews.sqlite3
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from curanews.db import SqliteArticleStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect CuraNews SQLite DB")
    parser.add_argument(
        "--sqlite",
        default="data/local/curanews.sqlite3",
        help="Path to SQLite database",
    )
    parser.add_argument("--limit", type=int, default=10, help="Rows to print")
    args = parser.parse_args(argv)

    path = Path(args.sqlite)
    if not path.is_file():
        print(f"Database not found: {path}", file=sys.stderr)
        return 1

    store = SqliteArticleStore(path)
    try:
        print(f"sqlite_rows={store.count()} path={path}")
        for row in store.list_recent(limit=args.limit):
            print(
                f"- {row.title!r} | {row.category} | {row.source} | {row.url}"
            )
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
