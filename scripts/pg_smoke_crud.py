"""CRUD smoke test against PostgreSQL (Issue #11 / G11).

Usage::

    docker compose up -d postgres
    poetry run alembic upgrade head
    poetry run python scripts/seed_sources.py
    poetry run python scripts/pg_smoke_crud.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from curanews.db.repository import ArticleRepository, SourceRepository
from curanews.db.session import get_session_factory
from curanews.db.sqlite_store import canonical_url_hash


def main() -> int:
    factory = get_session_factory()
    session = factory()
    try:
        sources = SourceRepository(session)
        articles = ArticleRepository(session)
        source = sources.get_by_name("example_news")
        if source is None:
            print("example_news source missing — run seed_sources.py first", file=sys.stderr)
            return 1

        inserted = articles.insert_article(
            source=source,
            title="PostgreSQL smoke headline",
            url="https://example.com/news/pg-smoke-2026",
            body="CRUD smoke body for Day 11.",
            summary="Smoke summary",
            category="tech",
            language="en",
            published_at=datetime(2026, 8, 7, tzinfo=timezone.utc),
        )
        session.commit()

        if inserted is None:
            row = articles.get_by_url_hash(
                canonical_url_hash("https://example.com/news/pg-smoke-2026")
            )
            status = "duplicate"
        else:
            row = inserted
            status = "inserted"

        payload = {
            "status": status,
            "article_id": str(row.id) if row else None,
            "title": row.title if row else None,
            "url_hash": row.url_hash if row else None,
            "total_articles": articles.count_articles(),
        }
        print(json.dumps(payload, indent=2))
        return 0 if row is not None else 1
    except Exception as exc:  # noqa: BLE001
        session.rollback()
        print(f"smoke crud failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
