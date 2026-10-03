"""Unit tests for Comments and Bookmarks APIs (Day 22)."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from tests.support.auth import bearer, create_account

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


@pytest.fixture(autouse=True)
def _no_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "curanews.api.routers.comments.get_redis_client",
        lambda: SimpleNamespace(available=False),
    )


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


def test_bookmarks_refuse_password_account_key(client: TestClient, session: Session) -> None:
    article = _seed_article(session)
    create_account(session, key="user-victim01")
    res = client.post(
        "/bookmarks", json={"article_id": str(article.id), "user_id": "user-victim01"}
    )
    assert res.status_code == 401
    assert client.get("/bookmarks?user_id=user-victim01").status_code == 401


def test_bookmark_unknown_article_is_404(client: TestClient) -> None:
    res = client.post("/bookmarks", json={"article_id": str(uuid4()), "user_id": "guest-abc123"})
    assert res.status_code == 404


def test_anonymous_comment_is_rejected(client: TestClient, session: Session) -> None:
    article = _seed_article(session)
    res = client.post(
        f"/articles/{article.id}/comments",
        json={"content": "Anonim yorum", "author_name": "Sahte Editör"},
    )
    assert res.status_code == 401


def test_comments_create_and_like(client: TestClient, session: Session) -> None:
    article = _seed_article(session)
    user = create_account(session, full_name="Ayşe Kaya")
    headers = bearer(user)

    post_res = client.post(
        f"/articles/{article.id}/comments",
        json={"content": "Çok bilgilendirici bir haber, tebrikler!", "author_name": "Başkası"},
        headers=headers,
    )
    assert post_res.status_code == 200
    comment = post_res.json()
    assert comment["content"] == "Çok bilgilendirici bir haber, tebrikler!"
    assert comment["author_name"] == "Ayşe Kaya"
    assert comment["likes"] == 0

    comment_id = comment["id"]
    assert client.post(f"/comments/{comment_id}/like").status_code == 401

    like_res = client.post(f"/comments/{comment_id}/like", headers=headers)
    assert like_res.status_code == 200
    assert like_res.json()["likes"] == 1

    repeat = client.post(f"/comments/{comment_id}/like", headers=headers)
    assert repeat.json()["likes"] == 1

    get_res = client.get(f"/articles/{article.id}/comments")
    assert get_res.status_code == 200
    assert get_res.json()["total"] == 1
    assert get_res.json()["items"][0]["likes"] == 1


def test_comment_rate_limit(client: TestClient, session: Session) -> None:
    article = _seed_article(session)
    headers = bearer(create_account(session))
    codes = [
        client.post(
            f"/articles/{article.id}/comments",
            json={"content": f"Yorum numarası {i}"},
            headers=headers,
        ).status_code
        for i in range(7)
    ]
    assert codes[:5] == [200] * 5
    assert codes[-1] == 429
