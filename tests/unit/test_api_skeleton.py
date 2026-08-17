"""FastAPI skeleton tests (Issue #16 / G16) — TestClient + in-memory SQLite."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from curanews.api.app import create_app
from curanews.api.deps import get_db
from curanews.db.base import Base
from curanews.db.entity_repository import EntityRepository
from curanews.db.models import Article, Source
from curanews.db.user_repository import UserRepository
from curanews.nlp.entities import ExtractedEntity


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


def _seed(session: Session) -> Article:
    source = Source(name="example_news", base_url="https://example.com/", kind="static")
    session.add(source)
    session.flush()
    article = Article(
        id=uuid4(),
        source_id=source.id,
        url="https://example.com/news/api-demo",
        url_hash="a" * 64,
        title="API demo headline",
        summary="Summary for API demo",
        body="Body about economy and markets.",
        content_hash="b" * 64,
        category="economy",
        published_at=datetime(2026, 8, 17, tzinfo=timezone.utc),
    )
    session.add(article)
    session.flush()
    EntityRepository(session).attach_extracted(
        article.id,
        [ExtractedEntity(label="TOPIC:economy", ent_type="TOPIC", normalized="economy", confidence=0.8)],
    )
    UserRepository(session).ensure_user("demo-user-a")
    session.commit()
    return article


def test_health_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["app"]
    assert body["status"] in {"ok", "degraded"}
    assert "database" in body
    assert "redis" in body


def test_openapi_lists_core_paths(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/health" in paths
    assert "/articles" in paths
    assert "/articles/{article_id}" in paths
    assert "/feed" in paths
    assert "/reads" in paths
    assert "/topics" in paths


def test_articles_and_feed_and_reads(client: TestClient, session: Session) -> None:
    article = _seed(session)

    listed = client.get("/articles")
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1

    detail = client.get(f"/articles/{article.id}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "API demo headline"

    feed = client.get("/feed", params={"user_id": "demo-user-a"})
    assert feed.status_code == 200
    payload = feed.json()
    assert payload["user_id"] == "demo-user-a"
    assert payload["cache"] == "miss"
    assert len(payload["items"]) >= 1

    read = client.post(
        "/reads",
        json={"user_id": "demo-user-a", "article_id": str(article.id), "dwell_ms": 1200},
    )
    assert read.status_code == 201
    assert read.json()["article_id"] == str(article.id)

    topics = client.get("/topics")
    assert topics.status_code == 200
    assert any(t["normalized"] == "economy" for t in topics.json()["items"])
