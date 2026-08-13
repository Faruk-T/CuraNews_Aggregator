"""Ingestion pipeline tests (Issue #13 / G13)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from curanews.db.base import Base
from curanews.db.repository import ArticleRepository
from curanews.domain.models import RawArticleDraft
from curanews.ingestion.pipeline import IngestionPipeline
from curanews.privacy.scrub import scrub_text
from curanews.scrapers.adapters.base import SourceAdapter


class _StubAdapter:
    source_id = "stub_source"
    kind: Literal["static"] = "static"

    def __init__(self, drafts: list[RawArticleDraft]) -> None:
        self._drafts = drafts

    def fetch(self, *, limit: int = 50) -> list[RawArticleDraft]:
        return self._drafts[:limit]


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()


def _valid_draft(url: str, *, title: str = "Headline") -> RawArticleDraft:
    return RawArticleDraft(
        title=title,
        url=url,
        content="Body text for ingestion pipeline.",
        published_date=datetime(2026, 8, 12, tzinfo=timezone.utc),
        source="stub_source",
        category="tech",
    )


def test_ingestion_inserts_valid_drafts(session: Session) -> None:
    adapter: SourceAdapter = _StubAdapter([_valid_draft("https://example.com/news/a")])
    pipeline = IngestionPipeline(session, invalidate_feed_cache=False, run_nlp=False)
    stats = pipeline.ingest_adapter(adapter, limit=5)

    assert stats.fetched == 1
    assert stats.promoted == 1
    assert stats.inserted == 1
    assert stats.duplicates == 0
    session.commit()

    articles = ArticleRepository(session)
    assert articles.count_articles() == 1


def test_ingestion_skips_duplicate_url_hash(session: Session) -> None:
    adapter: SourceAdapter = _StubAdapter(
        [
            _valid_draft("https://example.com/news/dup", title="First"),
            _valid_draft("https://example.com/news/dup", title="Second"),
        ]
    )
    pipeline = IngestionPipeline(session, invalidate_feed_cache=False, run_nlp=False)
    stats = pipeline.ingest_adapter(adapter, limit=5)

    assert stats.inserted == 1
    assert stats.duplicates == 1
    session.commit()
    assert ArticleRepository(session).count_articles() == 1


def test_ingestion_second_run_is_all_duplicates(session: Session) -> None:
    draft = _valid_draft("https://example.com/news/replay")
    adapter: SourceAdapter = _StubAdapter([draft])
    pipeline = IngestionPipeline(session, invalidate_feed_cache=False, run_nlp=False)

    first = pipeline.ingest_adapter(adapter, limit=5)
    assert first.inserted == 1

    second = pipeline.ingest_adapter(adapter, limit=5)
    assert second.inserted == 0
    assert second.duplicates == 1
    session.commit()
    assert ArticleRepository(session).count_articles() == 1


def test_ingestion_skips_incomplete_drafts(session: Session) -> None:
    adapter: SourceAdapter = _StubAdapter(
        [
            RawArticleDraft(title="Missing url"),
            _valid_draft("https://example.com/news/ok"),
        ]
    )
    pipeline = IngestionPipeline(session, invalidate_feed_cache=False, run_nlp=False)
    stats = pipeline.ingest_adapter(adapter, limit=5)

    assert stats.skipped_invalid == 1
    assert stats.inserted == 1
    session.commit()


def test_scrub_text_masks_email() -> None:
    masked = scrub_text("Contact reporter@example.com for details.")
    assert "[email-redacted]" in masked
    assert "reporter@example.com" not in masked
