"""One RSS refresh pass: pull every catalog feed and upsert new stories.

Run standalone (the API scheduler spawns it in a child process so spaCy
tagging never blocks request handling)::

    python -m curanews.ingestion.refresh
"""

from __future__ import annotations

import json
import sys

from sqlalchemy.orm import Session

from curanews.config import get_settings
from curanews.db.session import get_session_factory
from curanews.ingestion.pipeline import IngestionPipeline, IngestionStats
from curanews.ingestion.status import record_ingest_status, utc_now_iso
from curanews.logging_setup import setup_logging
from curanews.scrapers.adapters.rss_client import RssCatalogAdapter

COMMIT_EVERY = 25


def refresh_rss(
    session: Session,
    *,
    adapter: RssCatalogAdapter | None = None,
    limit: int | None = None,
) -> IngestionStats:
    pipeline = IngestionPipeline(session, commit_every=COMMIT_EVERY)
    stats = pipeline.ingest_adapter(
        adapter or RssCatalogAdapter(),
        limit=limit or get_settings().ingest_max_items,
    )
    session.commit()
    return stats


def stats_payload(stats: IngestionStats) -> dict[str, int | str]:
    return {
        "adapter": "rss_catalog (rss)",
        "fetched": stats.fetched,
        "promoted": stats.promoted,
        "inserted": stats.inserted,
        "duplicates": stats.duplicates,
        "skipped_invalid": stats.skipped_invalid,
        "failed": stats.failed,
        "entities_linked": stats.entities_linked,
    }


def main() -> int:
    setup_logging()
    started = utc_now_iso()
    record_ingest_status({"status": "running", "started_at": started})
    session = get_session_factory()()
    try:
        stats = refresh_rss(session)
    except Exception as exc:  # noqa: BLE001
        session.rollback()
        record_ingest_status(
            {
                "status": "error",
                "started_at": started,
                "finished_at": utc_now_iso(),
                "error": str(exc),
            }
        )
        print(f"rss refresh failed: {exc}", file=sys.stderr, flush=True)
        return 1
    finally:
        session.close()

    payload = stats_payload(stats)
    print(json.dumps(payload), flush=True)
    record_ingest_status(
        {
            "status": "ok" if stats.fetched else "empty",
            "started_at": started,
            "finished_at": utc_now_iso(),
            **payload,
        }
    )
    if stats.fetched == 0:
        print(
            "no RSS items fetched — check SCRAPE_ALLOWLIST_HOSTS and network",
            file=sys.stderr,
            flush=True,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
