"""Curation scoring and PII scrub tests (Issue #15 / G15)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from curanews.db.base import Base
from curanews.db.entity_repository import EntityRepository
from curanews.db.models import Article, Source
from curanews.db.user_repository import UserRepository
from curanews.nlp.curation import CurationEngine, freshness_score, jaccard
from curanews.nlp.entities import ExtractedEntity
from curanews.privacy.pii import (
    EMAIL_REDACTION,
    HANDLE_REDACTION,
    PHONE_REDACTION,
    scrub_pii,
)


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()


def test_scrub_pii_masks_email_phone_handle() -> None:
    raw = "Mail reporter@news.test or @editor_desk — call +1 (212) 555-0199 now."
    out = scrub_pii(raw)
    assert "reporter@news.test" not in out
    assert EMAIL_REDACTION in out
    assert "@editor_desk" not in out
    assert HANDLE_REDACTION in out
    assert "555-0199" not in out
    assert PHONE_REDACTION in out


def test_jaccard_and_freshness_helpers() -> None:
    assert jaccard({"economy", "ai"}, {"economy", "sports"}) == pytest.approx(1 / 3)
    now = datetime(2026, 8, 14, tzinfo=timezone.utc)
    fresh = freshness_score(now, now=now)
    assert fresh == pytest.approx(1.0)
    older = freshness_score(datetime(2026, 8, 1, tzinfo=timezone.utc), now=now)
    assert older < fresh


def _article(
    session: Session,
    source: Source,
    *,
    title: str,
    url_hash: str,
    entities: list[tuple[str, str]],
) -> Article:
    article = Article(
        id=uuid4(),
        source_id=source.id,
        url=f"https://example.com/{url_hash[:8]}",
        url_hash=url_hash,
        title=title,
        body=f"Body for {title}",
        summary=f"Summary for {title} with enough length",
        content_hash="x" * 64,
        category="news",
        published_at=datetime(2026, 8, 14, tzinfo=timezone.utc),
    )
    session.add(article)
    session.flush()
    EntityRepository(session).attach_extracted(
        article.id,
        [
            ExtractedEntity(
                label=f"{t}:{n}",
                ent_type=t,
                normalized=n.lower(),
                confidence=0.9,
            )
            for t, n in entities
        ],
    )
    return article


def test_user_a_and_b_rankings_differ(session: Session) -> None:
    source = Source(name="demo", base_url="https://example.com/", kind="static")
    session.add(source)
    session.flush()

    economy = _article(
        session,
        source,
        title="Economy headline",
        url_hash="e" * 64,
        entities=[("TOPIC", "economy"), ("TOPIC", "ai")],
    )
    sports = _article(
        session,
        source,
        title="Sports headline",
        url_hash="s" * 64,
        entities=[("TOPIC", "sports")],
    )
    climate = _article(
        session,
        source,
        title="Climate headline",
        url_hash="c" * 64,
        entities=[("TOPIC", "climate")],
    )

    users = UserRepository(session)
    user_a = users.ensure_user("demo-user-a")
    user_b = users.ensure_user("demo-user-b")
    users.record_read(user_a.id, economy.id)
    users.record_read(user_b.id, sports.id)
    session.commit()

    engine = CurationEngine(session)
    now = datetime(2026, 8, 14, 18, 0, tzinfo=timezone.utc)
    candidates = [economy, sports, climate]
    rank_a = [s.article.title for s in engine.rank(user_a.id, candidates, now=now)]
    rank_b = [s.article.title for s in engine.rank(user_b.id, candidates, now=now)]

    assert rank_a != rank_b
    assert rank_a[0] == "Economy headline"
    assert rank_b[0] == "Sports headline"

    hidden = [s.article.title for s in engine.rank(user_a.id, candidates, now=now, hide_read=True)]
    assert "Economy headline" not in hidden
    assert hidden[0] in {"Sports headline", "Climate headline"}
