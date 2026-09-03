"""Unit tests for Onedio-style Editor CMS API (Day 22)."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from curanews.api.app import create_app
from curanews.api.deps import get_db
from curanews.db.base import Base


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


def test_create_editorial_article(client: TestClient) -> None:
    payload = {
        "title": "Yapay Zeka ve Geleceğin Meslekleri: Özel Dosya",
        "category": "teknoloji",
        "summary": "CuraNews editör masasının hazırladığı kapsamlı yapay zeka analiz raporu.",
        "body": "Gelişen yapay zeka modelleri yazılım ve veri analitiğinde yeni kapılar açıyor.",
        "image_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800",
        "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "author_name": "Ahmet Yılmaz",
        "author_title": "Baş Editör",
        "author_avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
    }

    res = client.post("/editor/articles", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["title"] == payload["title"]
    assert data["category"] == "teknoloji"
    assert data["category_name"] == "Teknoloji"
    assert data["source_name"] == "CuraNews Editör Masası"
    assert data["is_editorial"] is True
    assert data["author_display"] == "Ahmet Yılmaz"
    assert data["author_title"] == "Baş Editör"
    assert data["video_url"] == payload["video_url"]
    assert data["image_url"] == payload["image_url"]
