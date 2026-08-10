"""Repository CRUD tests (in-memory SQLite ORM smoke)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from curanews.db.base import Base
from curanews.db.models import Article
from curanews.db.repository import ArticleRepository, SourceRepository
from curanews.db.sqlite_store import canonical_url_hash


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


def test_insert_and_select_by_url_hash(session: Session) -> None:
    sources = SourceRepository(session)
    articles = ArticleRepository(session)
    source = sources.ensure_source(
        name="example_news",
        base_url="https://example.com/",
        kind="static",
    )
    row = articles.insert_article(
        source=source,
        title="ORM smoke",
        url="https://example.com/news/orm-smoke",
        body="Body",
        category="tech",
        published_at=datetime(2026, 8, 7, tzinfo=timezone.utc),
    )
    assert row is not None
    session.commit()

    fetched = articles.get_by_url_hash(canonical_url_hash("https://example.com/news/orm-smoke"))
    assert fetched is not None
    assert fetched.title == "ORM smoke"
    assert isinstance(fetched, Article)


def test_duplicate_url_hash_returns_none(session: Session) -> None:
    sources = SourceRepository(session)
    articles = ArticleRepository(session)
    source = sources.ensure_source(name="demo", base_url="https://example.com/", kind="static")
    url = "https://example.com/news/dup"
    first = articles.insert_article(source=source, title="A", url=url, body="a")
    assert first is not None
    second = articles.insert_article(source=source, title="B", url=url, body="b")
    assert second is None
