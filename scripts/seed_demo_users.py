"""Seed demo users A/B and biased read history (Issue #15 / G15).

User A leans economy/AI; User B leans sports/climate — for curation demos.

Usage::

    poetry run alembic upgrade head
    poetry run python scripts/seed_sources.py
    poetry run python scripts/seed_demo_users.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4

from sqlalchemy import select

from curanews.db.entity_repository import EntityRepository
from curanews.db.models import Article, Source
from curanews.db.session import get_session_factory
from curanews.db.sqlite_store import canonical_url_hash
from curanews.db.user_repository import UserRepository
from curanews.nlp.entities import ExtractedEntity


def _content_hash(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _ensure_article(
    session,
    *,
    source: Source,
    title: str,
    url: str,
    body: str,
    category: str,
    entities: list[tuple[str, str]],
) -> Article:
    url_hash = canonical_url_hash(url)
    existing = session.scalars(select(Article).where(Article.url_hash == url_hash)).one_or_none()
    if existing is not None:
        article = existing
    else:
        article = Article(
            id=uuid4(),
            source_id=source.id,
            url=url,
            url_hash=url_hash,
            title=title,
            body=body,
            summary=body[:120],
            content_hash=_content_hash(body),
            category=category,
            language="en",
            published_at=datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc),
        )
        session.add(article)
        session.flush()

    repo = EntityRepository(session)
    extracted = [
        ExtractedEntity(
            label=f"{ent_type}:{label}",
            ent_type=ent_type,
            normalized=label.lower(),
            confidence=0.9,
        )
        for ent_type, label in entities
    ]
    repo.attach_extracted(article.id, extracted)
    return article


def main() -> int:
    factory = get_session_factory()
    session = factory()
    try:
        users = UserRepository(session)
        user_a = users.ensure_user("demo-user-a")
        user_b = users.ensure_user("demo-user-b")

        source = session.scalars(select(Source).where(Source.name == "example_news")).one_or_none()
        if source is None:
            source = Source(name="example_news", base_url="https://example.com/", kind="static")
            session.add(source)
            session.flush()

        economy = _ensure_article(
            session,
            source=source,
            title="Markets rally on rate-cut hopes",
            url="https://example.com/news/curation-economy-demo",
            body="Economy and markets react as interest rate policy shifts.",
            category="economy",
            entities=[("TOPIC", "economy"), ("TOPIC", "ai")],
        )
        sports = _ensure_article(
            session,
            source=source,
            title="Championship final ends in draw",
            url="https://example.com/news/curation-sports-demo",
            body="Sports fans packed the stadium for the championship final.",
            category="sports",
            entities=[("TOPIC", "sports")],
        )
        climate = _ensure_article(
            session,
            source=source,
            title="Coastal sensors track warming",
            url="https://example.com/news/curation-climate-demo",
            body="Climate scientists deploy sensors to track ocean warming.",
            category="climate",
            entities=[("TOPIC", "climate")],
        )
        tech = _ensure_article(
            session,
            source=source,
            title="Open-source models gain ground",
            url="https://example.com/news/curation-tech-demo",
            body="Artificial intelligence and technology markets expand with open source.",
            category="tech",
            entities=[("TOPIC", "ai"), ("TOPIC", "technology"), ("ORG", "openai")],
        )

        # Bias read history: A = economy/AI, B = sports/climate
        users.record_read(user_a.id, economy.id, dwell_ms=40_000)
        users.record_read(user_a.id, tech.id, dwell_ms=35_000)
        users.record_read(user_b.id, sports.id, dwell_ms=45_000)
        users.record_read(user_b.id, climate.id, dwell_ms=30_000)

        session.commit()
        print(
            json.dumps(
                {
                    "users": [
                        {"external_key": user_a.external_key, "id": str(user_a.id)},
                        {"external_key": user_b.external_key, "id": str(user_b.id)},
                    ],
                    "profile_a": sorted(users.entity_profile(user_a.id)),
                    "profile_b": sorted(users.entity_profile(user_b.id)),
                    "seed_articles": [
                        economy.title,
                        sports.title,
                        climate.title,
                        tech.title,
                    ],
                },
                indent=2,
            )
        )
        return 0
    except Exception as exc:  # noqa: BLE001
        session.rollback()
        print(f"seed demo users failed: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
