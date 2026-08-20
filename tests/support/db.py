"""SQLite session factories for deterministic tests (no Docker required)."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from curanews.db.base import Base
from curanews.db.entity_repository import EntityRepository
from curanews.db.models import Article, Source
from curanews.db.user_repository import UserRepository
from curanews.nlp.entities import ExtractedEntity


def make_sqlite_session() -> Session:
    """Create an isolated in-memory SQLite session with schema applied."""
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return factory()


def seed_source(session: Session, *, name: str = "example_news") -> Source:
    source = Source(name=name, base_url="https://example.com/", kind="static")
    session.add(source)
    session.flush()
    return source


def seed_article(
    session: Session,
    source: Source,
    *,
    title: str,
    url_path: str,
    url_hash: str,
    category: str,
    topics: list[str],
    published_at: datetime | None = None,
) -> Article:
    article = Article(
        id=uuid4(),
        source_id=source.id,
        url=f"https://example.com/{url_path.lstrip('/')}",
        url_hash=url_hash,
        title=title,
        summary=f"{title} summary with enough length for feed display",
        body=f"Body about {category}.",
        content_hash=uuid4().hex + uuid4().hex,
        category=category,
        published_at=published_at or datetime(2026, 8, 19, tzinfo=timezone.utc),
    )
    session.add(article)
    session.flush()
    EntityRepository(session).attach_extracted(
        article.id,
        [
            ExtractedEntity(
                label=f"TOPIC:{topic}",
                ent_type="TOPIC",
                normalized=topic.lower(),
                confidence=0.9,
            )
            for topic in topics
        ],
    )
    return article


def seed_demo_users(session: Session, *keys: str) -> None:
    users = UserRepository(session)
    for key in keys:
        users.ensure_user(key)


def sqlite_session_fixture() -> Generator[Session, None, None]:
    """Yield a clean session and always close it."""
    session = make_sqlite_session()
    try:
        yield session
    finally:
        session.close()
