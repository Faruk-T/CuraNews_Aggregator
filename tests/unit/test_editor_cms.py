"""Editor CMS API: access control and media validation."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from tests.support.auth import bearer, create_account

from curanews.api.app import create_app
from curanews.api.auth import create_access_token
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


PAYLOAD = {
    "title": "Yapay Zeka ve Geleceğin Meslekleri: Özel Dosya",
    "category": "teknoloji",
    "summary": "CuraNews editör masasının hazırladığı kapsamlı yapay zeka analiz raporu.",
    "body": "Gelişen yapay zeka modelleri yazılım ve veri analitiğinde yeni kapılar açıyor.",
    "image_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800",
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "author_title": "Baş Editör",
}


def test_editor_endpoint_requires_login(client: TestClient) -> None:
    res = client.post("/editor/articles", json=PAYLOAD)
    assert res.status_code == 401


def test_reader_cannot_publish(client: TestClient, session: Session) -> None:
    reader = create_account(session)
    res = client.post("/editor/articles", json=PAYLOAD, headers=bearer(reader))
    assert res.status_code == 403


def test_forged_role_claim_is_ignored(client: TestClient, session: Session) -> None:
    reader = create_account(session)
    token = create_access_token(reader.id, reader.external_key, role="editor")
    res = client.post(
        "/editor/articles", json=PAYLOAD, headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403


def test_create_editorial_article(client: TestClient, session: Session) -> None:
    editor = create_account(
        session,
        key="demo-editor",
        email="editor@example.com",
        role="editor",
        full_name="Ahmet Yılmaz",
    )
    res = client.post("/editor/articles", json=PAYLOAD, headers=bearer(editor))
    assert res.status_code == 200
    data = res.json()

    assert data["title"] == PAYLOAD["title"]
    assert data["category"] == "teknoloji"
    assert data["category_name"] == "Teknoloji"
    assert data["source_name"] == "CuraNews Editör Masası"
    assert data["is_editorial"] is True
    assert data["author_display"] == "Ahmet Yılmaz"
    assert data["author_title"] == "Baş Editör"
    assert data["video_url"] == "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
    assert data["image_url"] == PAYLOAD["image_url"]
    assert data["page_path"].startswith(f"haber/{data['id']}/yapay-zeka")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("video_url", "javascript:alert(1)"),
        ("video_url", "https://evil.example.com/embed/x"),
        ("image_url", "javascript:alert(1)"),
    ],
)
def test_editor_rejects_unsafe_media(
    client: TestClient, session: Session, field: str, value: str
) -> None:
    editor = create_account(session, key="demo-editor", role="editor")
    res = client.post("/editor/articles", json={**PAYLOAD, field: value}, headers=bearer(editor))
    assert res.status_code == 422
