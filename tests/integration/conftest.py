"""Shared fixtures for API integration tests (Issue #19 / G19)."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from curanews.api.app import create_app
from curanews.api.deps import get_db
from curanews.api.routers.feed import get_feed_cache
from curanews.cache.feed_cache import FeedCache
from tests.support.db import sqlite_session_fixture
from tests.support.fakes import FakeRedisClient


@pytest.fixture
def session() -> Generator[Session, None, None]:
    yield from sqlite_session_fixture()


@pytest.fixture
def fake_redis() -> FakeRedisClient:
    return FakeRedisClient()


@pytest.fixture
def feed_cache(fake_redis: FakeRedisClient) -> FeedCache:
    return FeedCache(client=fake_redis, ttl_seconds=120)  # type: ignore[arg-type]


@pytest.fixture
def client(session: Session, feed_cache: FeedCache) -> Generator[TestClient, None, None]:
    """TestClient with SQLite + FakeRedis overrides (no Docker)."""
    app = create_app()

    def _db() -> Generator[Session, None, None]:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_feed_cache] = lambda: feed_cache

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
