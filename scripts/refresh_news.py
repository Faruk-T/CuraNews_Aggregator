"""Refresh CuraNews with public RSS headlines.

Usage::

    docker compose up -d postgres redis
    poetry run alembic upgrade head
    poetry run python scripts/refresh_news.py              # RSS only (production)
    poetry run python scripts/refresh_news.py --with-demo  # + demo users A/B (local dev)
    poetry run python scripts/run_api.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from curanews.db.session import get_session_factory
from curanews.ingestion.pipeline import IngestionPipeline
from curanews.logging_setup import setup_logging
from curanews.scrapers.adapters.rss_client import RssCatalogAdapter

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-demo",
        action="store_true",
        help="also seed demo users and English placeholder stories (local dev only)",
    )
    args = parser.parse_args(argv)
    setup_logging()
    factory = get_session_factory()
    session = factory()
    try:
        pipeline = IngestionPipeline(session)
        stats = pipeline.ingest_adapter(RssCatalogAdapter(), limit=64)
        session.commit()
        print(
            json.dumps(
                {
                    "adapter": "rss_catalog (rss)",
                    "fetched": stats.fetched,
                    "promoted": stats.promoted,
                    "inserted": stats.inserted,
                    "duplicates": stats.duplicates,
                    "skipped_invalid": stats.skipped_invalid,
                    "entities_linked": stats.entities_linked,
                },
                indent=2,
            )
        )
        if stats.fetched == 0:
            print(
                "no RSS items fetched — check SCRAPE_ALLOWLIST_HOSTS and network",
                file=sys.stderr,
            )
            return 1
    except Exception as exc:  # noqa: BLE001
        session.rollback()
        print(f"refresh_news ingestion failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()

    if not args.with_demo:
        return 0
    demo = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "seed_demo_users.py")],
        cwd=ROOT,
        check=False,
    )
    return int(demo.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
