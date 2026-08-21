"""Personalized feed divergence via HTTP (Issue #19 / G19)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from curanews.db.user_repository import UserRepository
from tests.support.db import seed_article, seed_demo_users, seed_source


def test_api_feed_orders_differ_for_user_a_and_b(client: TestClient, session: Session) -> None:
    source = seed_source(session)
    economy = seed_article(
        session,
        source,
        title="Economy headline",
        url_path="economy",
        url_hash="e" * 64,
        category="economy",
        topics=["economy", "ai"],
    )
    sports = seed_article(
        session,
        source,
        title="Sports headline",
        url_path="sports",
        url_hash="s" * 64,
        category="sports",
        topics=["sports"],
    )
    seed_article(
        session,
        source,
        title="Climate headline",
        url_path="climate",
        url_hash="c" * 64,
        category="climate",
        topics=["climate"],
    )

    users = UserRepository(session)
    user_a = users.ensure_user("demo-user-a")
    user_b = users.ensure_user("demo-user-b")
    users.record_read(user_a.id, economy.id)
    users.record_read(user_b.id, sports.id)
    session.commit()

    feed_a = client.get("/feed", params={"user_id": "demo-user-a", "limit": 10})
    feed_b = client.get("/feed", params={"user_id": "demo-user-b", "limit": 10})
    assert feed_a.status_code == 200
    assert feed_b.status_code == 200

    titles_a = [i["title"] for i in feed_a.json()["items"]]
    titles_b = [i["title"] for i in feed_b.json()["items"]]
    assert titles_a != titles_b
    assert titles_a[0] == "Economy headline"
    assert titles_b[0] == "Sports headline"


def test_openapi_exposes_core_contract(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    for path in ("/health", "/articles", "/feed", "/reads", "/topics"):
        assert path in paths
