"""Unit tests for Comments and Bookmarks APIs (Day 22)."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from curanews.api.app import create_app
from curanews.api.deps import get_db
from curanews.db.base import Base
from curanews.db.models import Article, Source


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    app = create_app()

    def _override() -> Generator[Session, None, None]:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _seed_article(session: Session) -> Article:
    source = Source(name="test_source", base_url="https://test.com", kind="rss")
    session.add(source)
    session.flush()

    article = Article(
        source_id=source.id,
        url="https://test.com/news/1",
        url_hash=uuid4().hex,
        title="Test Haber Başlığı",
        summary="Test haber özeti.",
        body="Detaylı test haber metni.",
        content_hash=uuid4().hex,
        published_at=datetime.now(UTC),
        scraped_at=datetime.now(UTC),
        raw_metadata={},
    )
    session.add(article)
    session.commit()
    return article


def test_bookmark_toggle_and_list(client: TestClient, session: Session) -> None:
    article = _seed_article(session)

    # 1. Add to bookmarks
    res = client.post(
        "/bookmarks",
        json={"article_id": str(article.id), "user_id": "demo-user-a"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_bookmarked"] is True
    assert data["total_bookmarks"] == 1

    # 2. List bookmarks
    list_res = client.get("/bookmarks?user_id=demo-user-a")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] == 1
    assert list_data["items"][0]["id"] == str(article.id)

    # 3. Toggle off (remove from bookmarks)
    res_off = client.post(
        "/bookmarks",
        json={"article_id": str(article.id), "user_id": "demo-user-a"},
    )
    assert res_off.status_code == 200
    assert res_off.json()["is_bookmarked"] is False


def test_comments_create_and_like(client: TestClient, session: Session) -> None:
    article = _seed_article(session)

    # 1. Post a comment
    post_res = client.post(
        f"/articles/{article.id}/comments",
        json={"content": "Çok bilgilendirici bir haber, tebrikler!", "author_name": "Ayşe Kaya"},
    )
    assert post_res.status_code == 200
    comment = post_res.json()
    assert comment["content"] == "Çok bilgilendirici bir haber, tebrikler!"
    assert comment["author_name"] == "Ayşe Kaya"
    assert comment["likes"] == 0

    comment_id = comment["id"]

    # 2. Like the comment
    like_res = client.post(f"/comments/{comment_id}/like")
    assert like_res.status_code == 200
    assert like_res.json()["likes"] == 1

    # 3. List comments
    get_res = client.get(f"/articles/{article.id}/comments")
    assert get_res.status_code == 200
    assert get_res.json()["total"] == 1
    assert get_res.json()["items"][0]["likes"] == 1
