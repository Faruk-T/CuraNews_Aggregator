"""Seed demo sources into PostgreSQL (Issue #11 / G11).

Usage::

    poetry run alembic upgrade head
    poetry run python scripts/seed_sources.py
"""

from __future__ import annotations

import json
import sys

from curanews.db.repository import SourceRepository
from curanews.db.session import get_session_factory


def main() -> int:
    factory = get_session_factory()
    session = factory()
    try:
        repo = SourceRepository(session)
        seeds = [
            ("example_news", "https://example.com/", "static"),
            ("dynamic_demo", "file://fixtures/dynamic_news_scroll.html", "dynamic"),
            ("gnews_api", "https://gnews.io/api/v4/top-headlines", "api"),
        ]
        rows = []
        for name, base_url, kind in seeds:
            source = repo.ensure_source(name=name, base_url=base_url, kind=kind)
            rows.append({"name": source.name, "kind": source.kind, "id": str(source.id)})
        session.commit()
        print(json.dumps({"seeded_sources": rows}, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001
        session.rollback()
        print(f"seed failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
