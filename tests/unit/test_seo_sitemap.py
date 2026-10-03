"""Unit tests for SEO, Sitemap, Robots.txt, RSS 2.0, and ads.txt (Day 23)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
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
from curanews.config import get_settings
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


def _seed_sample_articles(session: Session) -> None:
    source = Source(name="hurriyet", base_url="https://hurriyet.com.tr", kind="rss")
    session.add(source)
    session.flush()

    for i in range(3):
        art = Article(
            source_id=source.id,
            url=f"https://hurriyet.com.tr/haber/{i}",
            url_hash=uuid4().hex,
            title=f"Test Haber Başlığı {i}",
            summary=f"Özet metin {i}",
            body=f"Detaylı gövde {i}",
            category="ekonomi",
            content_hash=uuid4().hex,
            published_at=datetime.now(UTC),
            scraped_at=datetime.now(UTC),
            raw_metadata={"image_url": "https://example.com/test.jpg"},
        )
        session.add(art)
    session.commit()


def test_robots_txt(client: TestClient) -> None:
    res = client.get("/robots.txt")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/plain")
    text = res.text
    assert "User-agent: *" in text
    assert "Allow: /" in text
    assert "Disallow: /auth/" in text
    assert "Disallow: /editor/" in text
    assert "Sitemap: http://testserver/sitemap.xml" in text


def test_ads_txt_is_absent_without_publisher_id(client: TestClient) -> None:
    assert client.get("/ads.txt").status_code == 404


def test_ads_txt_with_publisher_id(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "adsense_pub_id", "ca-pub-1234567890123456")
    res = client.get("/ads.txt")
    assert res.status_code == 200
    assert res.text.strip() == "google.com, pub-1234567890123456, DIRECT, f08c47fec0942fa0"


def test_sitemap_lists_only_own_urls(client: TestClient, session: Session) -> None:
    _seed_sample_articles(session)
    res = client.get("/sitemap.xml")
    assert res.status_code == 200
    assert "application/xml" in res.headers["content-type"]

    root = ET.fromstring(res.text)
    assert root.tag.endswith("urlset")

    locs = [elem.text or "" for elem in root.iter() if elem.tag.endswith("loc")]
    assert len(locs) == 1 + 7 + 3
    assert all(loc.startswith("http://testserver/") for loc in locs)
    assert "http://testserver/ui/" in locs
    assert "http://testserver/kategori/ekonomi" in locs
    article_locs = [loc for loc in locs if "/haber/" in loc]
    assert len(article_locs) == 3
    assert all("test-haber-basligi-" in loc for loc in article_locs)


def test_rss_xml(client: TestClient, session: Session) -> None:
    _seed_sample_articles(session)
    res = client.get("/rss.xml")
    assert res.status_code == 200
    assert "application/rss+xml" in res.headers["content-type"]

    # Verify RSS XML is well-formed
    root = ET.fromstring(res.text)
    assert root.tag == "rss"
    channel = root.find("channel")
    assert channel is not None
    assert channel.find("title") is not None
    items = channel.findall("item")
    assert len(items) == 3
    assert items[0].find("title") is not None
    assert items[0].find("enclosure") is not None
    link = items[0].findtext("link") or ""
    assert link.startswith("http://testserver/haber/")
    assert "hurriyet.com.tr" not in link
