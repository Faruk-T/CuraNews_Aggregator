"""G19 acceptance suite — exact names from IMPLEMENTATION_PLAN §12.2."""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Literal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from curanews.db.repository import ArticleRepository
from curanews.db.user_repository import UserRepository
from curanews.domain.models import RawArticleDraft
from curanews.ingestion.pipeline import IngestionPipeline
from curanews.nlp.curation import CurationEngine
from curanews.privacy.pii import EMAIL_REDACTION, scrub_pii
from curanews.resilience import BackoffPolicy
from curanews.scrapers.adapters.base import SourceAdapter
from tests.support.db import seed_article, seed_demo_users, seed_source


@pytest.mark.unit
def test_backoff_increases() -> None:
    """§12.2 #1 — exponential backoff delays strictly increase (no jitter)."""
    policy = BackoffPolicy(base_seconds=0.5, cap_seconds=60, max_retries=5, jitter_ratio=0.0)
    delays = policy.iter_delays(rng=random.Random(0))
    assert delays == [0.5, 1.0, 2.0, 4.0, 8.0]
    assert delays == sorted(delays)
    assert delays[0] < delays[-1]


@pytest.mark.unit
def test_pii_masks_email() -> None:
    """§12.2 #2 — email addresses are redacted before any persist/serve path."""
    raw = "Contact editor@curanews.test for corrections."
    out = scrub_pii(raw)
    assert "editor@curanews.test" not in out
    assert EMAIL_REDACTION in out


@pytest.mark.integration
def test_dedupe_same_url(session: Session) -> None:
    """§12.2 #3 — identical URLs collapse to one row via url_hash."""

    class _DupAdapter:
        source_id = "dedupe_source"
        kind: Literal["static"] = "static"

        def fetch(self, *, limit: int = 50) -> list[RawArticleDraft]:
            draft = RawArticleDraft(
                title="Same URL twice",
                url="https://example.com/news/same-url",
                content="Body for dedupe acceptance test.",
                published_date=datetime(2026, 8, 19, tzinfo=timezone.utc),
                source=self.source_id,
                category="tech",
            )
            return [draft, draft][:limit]

    adapter: SourceAdapter = _DupAdapter()  # type: ignore[assignment]
    pipeline = IngestionPipeline(session, invalidate_feed_cache=False, run_nlp=False)
    stats = pipeline.ingest_adapter(adapter, limit=10)
    session.commit()

    assert stats.inserted == 1
    assert stats.duplicates == 1
    assert ArticleRepository(session).count_articles() == 1


@pytest.mark.integration
def test_curation_orders_differ_for_two_users(session: Session) -> None:
    """§12.2 #4 — User A and User B receive different ranking from the same corpus."""
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
    climate = seed_article(
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

    engine = CurationEngine(session)
    now = datetime(2026, 8, 19, 18, 0, tzinfo=timezone.utc)
    candidates = [economy, sports, climate]
    rank_a = [s.article.title for s in engine.rank(user_a.id, candidates, now=now)]
    rank_b = [s.article.title for s in engine.rank(user_b.id, candidates, now=now)]

    assert rank_a != rank_b
    assert rank_a[0] == "Economy headline"
    assert rank_b[0] == "Sports headline"


@pytest.mark.integration
def test_health_ok(client: TestClient) -> None:
    """§12.2 #5 — /health is reachable and returns a structured payload."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["app"]
    assert "version" in body
    assert body["database"] in {"up", "down"}
    assert body["redis"] in {"up", "down"}


@pytest.mark.integration
def test_feed_shape(client: TestClient, session: Session) -> None:
    """§12.2 #6 — /feed returns contract fields required by UI and cache layer."""
    source = seed_source(session)
    seed_article(
        session,
        source,
        title="Feed shape article",
        url_path="feed-shape",
        url_hash="f" * 64,
        category="economy",
        topics=["economy"],
    )
    seed_demo_users(session, "demo-user-a")
    session.commit()

    response = client.get("/feed", params={"user_id": "demo-user-a", "limit": 5})
    assert response.status_code == 200
    payload = response.json()

    assert set(payload) >= {"user_id", "generated_at", "cache", "items"}
    assert payload["user_id"] == "demo-user-a"
    assert payload["cache"] in {"hit", "miss", "bypass"}
    assert isinstance(payload["items"], list)
    assert len(payload["items"]) >= 1

    item = payload["items"][0]
    for key in ("id", "title", "url", "source_name", "entities"):
        assert key in item
    assert item["title"] == "Feed shape article"
    assert isinstance(payload["read_items"], list)
    assert payload["inbox_grace_seconds"] == 1200
    assert response.headers.get("X-Cache") in {"hit", "miss", "bypass"}
