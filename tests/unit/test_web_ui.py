"""Web UI shell, server-rendered pages and security headers."""

from __future__ import annotations

import json
import re
from collections.abc import Generator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from tests.support.db import sqlite_session_fixture
from tests.support.fakes import FakeRedisClient

from curanews.api.app import create_app
from curanews.api.deps import get_db
from curanews.api.routers.feed import get_feed_cache
from curanews.api.services import recategorize_articles
from curanews.api.urls import slugify
from curanews.cache.feed_cache import FeedCache
from curanews.db.models import Article, Source


@pytest.fixture
def session() -> Generator[Session, None, None]:
    yield from sqlite_session_fixture()


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    app = create_app()
    cache = FeedCache(client=FakeRedisClient(), ttl_seconds=60)  # type: ignore[arg-type]

    def _db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_feed_cache] = lambda: cache
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _seed(session: Session, *, title: str = "İsrail Başbakanı Netanyahu'dan açıklama") -> Article:
    source = Source(name="bbc_turkce", base_url="https://www.bbc.com/turkce", kind="rss")
    session.add(source)
    session.flush()
    article = Article(
        source_id=source.id,
        url=f"https://www.bbc.com/turkce/{uuid4().hex}",
        url_hash=uuid4().hex,
        title=title,
        summary="Netanyahu Gazze'deki ateşkes görüşmelerine ilişkin açıklama yaptı.",
        body=(
            "Netanyahu Gazze'deki ateşkes görüşmelerine ilişkin açıklama yaptı.\n\nİkinci paragraf."
        ),
        content_hash=uuid4().hex,
        category="gundem",
        published_at=datetime.now(UTC),
        scraped_at=datetime.now(UTC),
        raw_metadata={"image_url": "https://example.com/a.jpg"},
    )
    session.add(article)
    session.commit()
    return article


def _json_ld(html: str) -> list[dict]:
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    return [json.loads(block) for block in blocks]


def test_home_is_server_rendered(client: TestClient, session: Session) -> None:
    article = _seed(session)
    res = client.get("/ui/")
    assert res.status_code == 200
    html = res.text
    assert "<!--SSR:" not in html
    assert "__ASSET_VERSION__" not in html
    assert '<link rel="canonical" href="http://testserver/ui/"' in html
    assert '<h1 id="feedHeading"' in html
    assert article.title.replace("'", "&#x27;") in html
    assert f'href="../haber/{article.id}/{slugify(article.title)}"' in html
    assert 'id="featuredSlot" class="featured" hidden' not in html
    for word in ("editor123", "faruk123", "okur123", "pub-8573920194827104", "G-CURANEWS"):
        assert word not in html


def test_home_renders_without_articles(client: TestClient) -> None:
    res = client.get("/ui/")
    assert res.status_code == 200
    assert "feedList" in res.text
    assert 'id="featuredSlot" class="featured" hidden' in res.text


def test_article_page(client: TestClient, session: Session) -> None:
    article = _seed(session)
    slug = slugify(article.title)
    res = client.get(f"/haber/{article.id}/{slug}")
    assert res.status_code == 200
    html = res.text
    assert f'<link rel="canonical" href="http://testserver/haber/{article.id}/{slug}"' in html
    assert '<h1 class="page-title">' in html
    assert '<div class="page-body"><p>İkinci paragraf.</p></div>' in html
    graph = _json_ld(html)[0]["@graph"]
    news = next(node for node in graph if node["@type"] == "NewsArticle")
    assert news["articleSection"] == "Dünya"
    assert news["isBasedOn"] == article.url
    assert any(node["@type"] == "BreadcrumbList" for node in graph)


def test_article_slug_redirects(client: TestClient, session: Session) -> None:
    article = _seed(session)
    slug = slugify(article.title)
    wrong = client.get(f"/haber/{article.id}/eski-baslik", follow_redirects=False)
    assert wrong.status_code == 301
    assert wrong.headers["location"].endswith(slug)
    bare = client.get(f"/haber/{article.id}", follow_redirects=False)
    assert bare.status_code == 301
    assert bare.headers["location"].endswith(f"{article.id}/{slug}")


def test_missing_article_is_noindex_404(client: TestClient) -> None:
    res = client.get(f"/haber/{uuid4()}/yok")
    assert res.status_code == 404
    assert 'content="noindex, follow"' in res.text


def test_category_page(client: TestClient, session: Session) -> None:
    article = _seed(session)
    assert recategorize_articles(session) == 1
    assert recategorize_articles(session) == 0
    res = client.get("/kategori/dunya")
    assert res.status_code == 200
    assert "<h1>Dünya Haberleri</h1>" in res.text
    assert article.title.replace("'", "&#x27;") in res.text
    assert client.get("/kategori/bilinmeyen").status_code == 404


def test_root_redirects_to_ui(client: TestClient) -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"].endswith("/ui/")


def test_security_headers(client: TestClient) -> None:
    res = client.get("/ui/")
    assert res.headers["x-content-type-options"] == "nosniff"
    assert res.headers["x-frame-options"] == "SAMEORIGIN"
    csp = res.headers["content-security-policy"]
    assert "script-src 'self'" in csp
    assert "unsafe-inline" not in csp.split("script-src", 1)[1].split(";", 1)[0]
    assert "<script>" not in res.text
    assert "onerror=" not in res.text


def test_ui_assets_are_served(client: TestClient) -> None:
    css = client.get("/ui/styles.css")
    js = client.get("/ui/app.js")
    assert css.status_code == 200
    assert "--brand" in css.text
    assert js.status_code == 200
    assert "loadFeed" in js.text
    for asset in ("page.js", "favicon.svg"):
        assert client.get(f"/ui/{asset}").status_code == 200
    for image in ("og-default.png", "logo-512.png"):
        res = client.get(f"/ui/{image}")
        assert res.status_code == 200
        assert res.headers["content-type"] == "image/png"
