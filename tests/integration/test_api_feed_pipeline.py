"""End-to-end API flows: ingest → feed → read → cache (Issue #19 / G19)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from typing import Literal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from curanews.cache.feed_cache import FeedCache
from curanews.db.models import UserRead
from curanews.db.repository import ArticleRepository
from curanews.db.user_repository import UserRepository
from curanews.domain.models import RawArticleDraft
from curanews.ingestion.pipeline import IngestionPipeline
from curanews.scrapers.adapters.base import SourceAdapter
from tests.support.db import seed_article, seed_demo_users, seed_source
from tests.support.fakes import FakeRedisClient


class _SeedAdapter:
    source_id = "integration_source"
    kind: Literal["static"] = "static"

    def __init__(self, drafts: list[RawArticleDraft]) -> None:
        self._drafts = drafts

    def fetch(self, *, limit: int = 50) -> list[RawArticleDraft]:
        return self._drafts[:limit]


def test_ingest_then_list_articles_via_api(client: TestClient, session: Session) -> None:
    drafts = [
        RawArticleDraft(
            title="Ingested via pipeline",
            url="https://example.com/news/ingested-1",
            content="Body after cleaning path.",
            published_date=datetime(2026, 8, 19, tzinfo=timezone.utc),
            source="integration_source",
            category="tech",
        )
    ]
    adapter: SourceAdapter = _SeedAdapter(drafts)  # type: ignore[assignment]
    stats = IngestionPipeline(session, invalidate_feed_cache=False, run_nlp=False).ingest_adapter(
        adapter, limit=5
    )
    seed_demo_users(session, "demo-user-a")
    session.commit()

    assert stats.inserted == 1
    listed = client.get("/articles", params={"limit": 10})
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] >= 1
    assert any(item["title"] == "Ingested via pipeline" for item in body["items"])


def test_feed_miss_hit_then_read_invalidates(
    client: TestClient,
    session: Session,
    feed_cache: FeedCache,
    fake_redis: FakeRedisClient,
) -> None:
    source = seed_source(session)
    economy = seed_article(
        session,
        source,
        title="Economy rally",
        url_path="economy",
        url_hash="e" * 64,
        category="economy",
        topics=["economy"],
    )
    sports = seed_article(
        session,
        source,
        title="Sports final",
        url_path="sports",
        url_hash="s" * 64,
        category="sports",
        topics=["sports"],
    )
    seed_demo_users(session, "demo-user-a")
    session.commit()

    first = client.get("/feed", params={"user_id": "demo-user-a", "limit": 5})
    assert first.status_code == 200
    assert first.json()["cache"] == "miss"
    assert first.headers.get("X-Cache") == "miss"

    second = client.get("/feed", params={"user_id": "demo-user-a", "limit": 5})
    assert second.json()["cache"] == "hit"
    assert second.headers.get("X-Cache") == "hit"

    read = client.post(
        "/reads",
        json={"user_id": "demo-user-a", "article_id": str(sports.id), "dwell_ms": 4000},
    )
    assert read.status_code == 201

    third = client.get("/feed", params={"user_id": "demo-user-a", "limit": 5})
    assert third.json()["cache"] == "miss"
    by_title = {i["title"]: i for i in third.json()["items"]}
    assert "Sports final" in by_title
    assert by_title["Sports final"]["read"] is True
    assert by_title["Sports final"]["read_at"] is not None
    assert by_title["Economy rally"]["read"] is False
    assert economy.title in {i["title"] for i in third.json()["items"]}
    assert "Sports final" in {i["title"] for i in third.json()["read_items"]}
    # Fake redis still available — not a BYPASS path
    assert fake_redis.available is True
    assert feed_cache.ttl_seconds == 120


def test_redis_bypass_when_unavailable(
    client: TestClient,
    session: Session,
    fake_redis: FakeRedisClient,
) -> None:
    source = seed_source(session)
    seed_article(
        session,
        source,
        title="Bypass article",
        url_path="bypass",
        url_hash="b" * 64,
        category="tech",
        topics=["tech"],
    )
    seed_demo_users(session, "demo-user-a")
    session.commit()

    fake_redis.set_available(False)
    response = client.get("/feed", params={"user_id": "demo-user-a", "limit": 3})
    assert response.status_code == 200
    assert response.json()["cache"] == "bypass"
    assert response.headers.get("X-Cache") == "bypass"


def test_unknown_user_returns_404(client: TestClient, session: Session) -> None:
    seed_source(session)
    session.commit()
    response = client.get("/feed", params={"user_id": "missing-user", "limit": 5})
    assert response.status_code == 404


def test_topics_endpoint_after_seed(client: TestClient, session: Session) -> None:
    source = seed_source(session)
    seed_article(
        session,
        source,
        title="Topic article",
        url_path="topics",
        url_hash="t" * 64,
        category="economy",
        topics=["economy"],
    )
    session.commit()
    response = client.get("/topics")
    assert response.status_code == 200
    assert any(t["normalized"] == "economy" for t in response.json()["items"])
    assert ArticleRepository(session).count_articles() == 1


def test_feed_shows_publisher_not_adapter_key(client: TestClient, session: Session) -> None:
    source = seed_source(session, name="rss_catalog")
    article = seed_article(
        session,
        source,
        title="Publisher label article",
        url_path="publisher-label",
        url_hash="p" * 64,
        category="world",
        topics=["world"],
    )
    article.raw_metadata = {"publisher": "BBC News", "provider": "rss"}
    seed_demo_users(session, "demo-user-a")
    session.commit()

    response = client.get("/feed", params={"user_id": "demo-user-a", "limit": 5})
    assert response.status_code == 200
    assert response.json()["items"][0]["source_name"] == "BBC News"


def test_stale_read_leaves_inbox_after_grace(client: TestClient, session: Session) -> None:
    source = seed_source(session)
    article = seed_article(
        session,
        source,
        title="Aged read article",
        url_path="aged-read",
        url_hash="a" * 64,
        category="world",
        topics=["world"],
    )
    seed_article(
        session,
        source,
        title="Unread sibling",
        url_path="unread-sibling",
        url_hash="u" * 64,
        category="world",
        topics=["world"],
    )
    seed_demo_users(session, "demo-user-a")
    session.commit()

    posted = client.post(
        "/reads",
        json={"user_id": "demo-user-a", "article_id": str(article.id), "dwell_ms": 1000},
    )
    assert posted.status_code == 201

    session.expire_all()
    user = UserRepository(session).get_by_external_key("demo-user-a")
    assert user is not None
    row = session.scalars(
        select(UserRead).where(
            UserRead.user_id == user.id,
            UserRead.article_id == article.id,
        )
    ).one()
    row.read_at = datetime.now(UTC) - timedelta(minutes=21)
    session.commit()

    feed = client.get("/feed", params={"user_id": "demo-user-a", "limit": 5})
    assert feed.status_code == 200
    titles = [i["title"] for i in feed.json()["items"]]
    read_titles = [i["title"] for i in feed.json()["read_items"]]
    assert "Aged read article" not in titles
    assert "Unread sibling" in titles
    assert "Aged read article" in read_titles
