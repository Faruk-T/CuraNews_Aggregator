"""API feed cache integration tests (Issue #17 / G17)."""

from __future__ import annotations

import time
from collections.abc import Generator
from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from curanews.api.app import create_app
from curanews.api.deps import get_db
from curanews.api.routers.feed import get_feed_cache
from curanews.cache.feed_cache import FeedCache
from curanews.db.base import Base
from curanews.db.entity_repository import EntityRepository
from curanews.db.models import Article, Source, UserRead
from curanews.db.user_repository import UserRepository
from curanews.nlp.entities import ExtractedEntity


class FakeRedisClient:
    def __init__(self) -> None:
        self._available = True
        self._store: dict[str, str] = {}
        self._expiry: dict[str, float] = {}

    @property
    def available(self) -> bool:
        return self._available

    def _purge(self, key: str) -> None:
        expires_at = self._expiry.get(key)
        if expires_at is not None and time.monotonic() >= expires_at:
            self._store.pop(key, None)
            self._expiry.pop(key, None)

    def get(self, key: str) -> str | None:
        self._purge(key)
        return self._store.get(key)

    def setex(self, key: str, ttl_seconds: int, value: str) -> bool:
        self._store[key] = value
        self._expiry[key] = time.monotonic() + ttl_seconds
        return True

    def delete(self, key: str) -> bool:
        existed = key in self._store
        self._store.pop(key, None)
        self._expiry.pop(key, None)
        return existed

    def delete_by_prefix(self, prefix: str) -> int:
        keys = [k for k in list(self._store) if k.startswith(prefix)]
        for key in keys:
            self.delete(key)
        return len(keys)

    def exists(self, key: str) -> bool:
        self._purge(key)
        return key in self._store


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
def fake_cache() -> FeedCache:
    return FeedCache(client=FakeRedisClient(), ttl_seconds=120)  # type: ignore[arg-type]


@pytest.fixture
def client(session: Session, fake_cache: FeedCache) -> Generator[TestClient, None, None]:
    app = create_app()

    def _db() -> Generator[Session, None, None]:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_feed_cache] = lambda: fake_cache
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _seed_two_articles(session: Session) -> tuple[Article, Article]:
    source = Source(name="example_news", base_url="https://example.com/", kind="static")
    session.add(source)
    session.flush()

    economy = Article(
        id=uuid4(),
        source_id=source.id,
        url="https://example.com/news/economy",
        url_hash="e" * 64,
        title="Economy rally",
        summary="Markets and economy update with enough length",
        body="Economy body",
        content_hash="1" * 64,
        category="economy",
        published_at=datetime(2026, 8, 18, tzinfo=timezone.utc),
    )
    sports = Article(
        id=uuid4(),
        source_id=source.id,
        url="https://example.com/news/sports",
        url_hash="s" * 64,
        title="Sports final",
        summary="Championship sports coverage with enough length",
        body="Sports body",
        content_hash="2" * 64,
        category="sports",
        published_at=datetime(2026, 8, 18, tzinfo=timezone.utc),
    )
    session.add_all([economy, sports])
    session.flush()
    ents = EntityRepository(session)
    ents.attach_extracted(
        economy.id,
        [ExtractedEntity(label="TOPIC:economy", ent_type="TOPIC", normalized="economy", confidence=0.9)],
    )
    ents.attach_extracted(
        sports.id,
        [ExtractedEntity(label="TOPIC:sports", ent_type="TOPIC", normalized="sports", confidence=0.9)],
    )
    UserRepository(session).ensure_user("demo-user-a")
    session.commit()
    return economy, sports


def test_feed_miss_then_hit_and_x_cache_header(client: TestClient, session: Session) -> None:
    _seed_two_articles(session)

    first = client.get("/feed", params={"user_id": "demo-user-a", "limit": 5})
    assert first.status_code == 200
    assert first.json()["cache"] == "miss"
    assert first.headers.get("X-Cache") == "miss"

    second = client.get("/feed", params={"user_id": "demo-user-a", "limit": 5})
    assert second.status_code == 200
    assert second.json()["cache"] == "hit"
    assert second.headers.get("X-Cache") == "hit"
    assert [i["title"] for i in first.json()["items"]] == [i["title"] for i in second.json()["items"]]


def test_read_invalidates_cache_and_can_change_ranking(
    client: TestClient, session: Session
) -> None:
    economy, sports = _seed_two_articles(session)

    before = client.get("/feed", params={"user_id": "demo-user-a", "limit": 5})
    assert before.json()["cache"] == "miss"
    titles_before = [i["title"] for i in before.json()["items"]]
    assert "Sports final" in titles_before

    # Consuming an item keeps it on the main feed for the 20-minute grace window.
    read = client.post(
        "/reads",
        json={"user_id": "demo-user-a", "article_id": str(sports.id), "dwell_ms": 5000},
    )
    assert read.status_code == 201

    after = client.get("/feed", params={"user_id": "demo-user-a", "limit": 5})
    assert after.json()["cache"] == "miss"  # invalidated → recompute
    titles_after = [i["title"] for i in after.json()["items"]]
    by_title = {i["title"]: i for i in after.json()["items"]}
    assert "Sports final" in titles_after
    assert by_title["Sports final"]["read"] is True
    assert by_title["Sports final"]["read_at"] is not None
    assert by_title["Economy rally"]["read"] is False
    assert titles_before != titles_after or by_title["Sports final"]["read"] is True
    read_titles = [i["title"] for i in after.json()["read_items"]]
    assert "Sports final" in read_titles
    assert after.json()["inbox_grace_seconds"] == 1200


def test_stale_read_leaves_inbox_but_stays_in_read_items(
    client: TestClient, session: Session
) -> None:
    economy, sports = _seed_two_articles(session)
    posted = client.post(
        "/reads",
        json={"user_id": "demo-user-a", "article_id": str(sports.id), "dwell_ms": 5000},
    )
    assert posted.status_code == 201

    session.expire_all()
    user = UserRepository(session).get_by_external_key("demo-user-a")
    assert user is not None
    row = session.scalars(
        select(UserRead).where(
            UserRead.user_id == user.id,
            UserRead.article_id == sports.id,
        )
    ).one()
    row.read_at = datetime.now(UTC) - timedelta(minutes=21)
    session.commit()

    feed = client.get("/feed", params={"user_id": "demo-user-a", "limit": 5})
    assert feed.status_code == 200
    titles = [i["title"] for i in feed.json()["items"]]
    read_titles = [i["title"] for i in feed.json()["read_items"]]
    assert "Sports final" not in titles
    assert "Economy rally" in titles
    assert "Sports final" in read_titles
    assert all(i["read"] is True for i in feed.json()["read_items"] if i["title"] == "Sports final")
