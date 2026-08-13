"""Run adapter → PostgreSQL ingestion (Issue #13 / G13).

Usage::

    docker compose up -d postgres
    poetry run alembic upgrade head
    poetry run python scripts/seed_sources.py
    poetry run python scripts/run_ingestion.py --adapter static
    poetry run python scripts/run_ingestion.py --adapter static  # duplicates only
"""

from __future__ import annotations

import argparse
import json
import sys

from curanews.db.session import get_session_factory
from curanews.ingestion.pipeline import IngestionPipeline
from curanews.logging_setup import setup_logging
from curanews.scrapers.adapters import adapter_label, get_adapter, list_adapters


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest adapter drafts into PostgreSQL")
    parser.add_argument("--adapter", default="static", help="Adapter name (see --list)")
    parser.add_argument("--limit", type=int, default=10, help="Max drafts to fetch")
    parser.add_argument("--list", action="store_true", help="List registered adapters")
    parser.add_argument(
        "--no-cache-invalidate",
        action="store_true",
        help="Skip feed:* Redis invalidation after inserts",
    )
    parser.add_argument(
        "--no-nlp",
        action="store_true",
        help="Skip spaCy/topic tagging after insert (G14)",
    )
    args = parser.parse_args(argv)

    if args.list:
        for name in list_adapters():
            adapter = get_adapter(name)
            print(f"{name}\t{adapter_label(adapter)}")
        return 0

    setup_logging()
    adapter = get_adapter(args.adapter)
    factory = get_session_factory()
    session = factory()
    try:
        pipeline = IngestionPipeline(
            session,
            invalidate_feed_cache=not args.no_cache_invalidate,
            run_nlp=not args.no_nlp,
        )
        stats = pipeline.ingest_adapter(adapter, limit=max(1, args.limit))
        session.commit()
        payload = {
            "adapter": adapter_label(adapter),
            "fetched": stats.fetched,
            "promoted": stats.promoted,
            "inserted": stats.inserted,
            "duplicates": stats.duplicates,
            "skipped_invalid": stats.skipped_invalid,
            "feed_keys_invalidated": stats.feed_keys_invalidated,
            "entities_linked": stats.entities_linked,
        }
        print(json.dumps(payload, indent=2))
        return 0 if stats.persisted else 1
    except Exception as exc:  # noqa: BLE001
        session.rollback()
        print(f"ingestion failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
