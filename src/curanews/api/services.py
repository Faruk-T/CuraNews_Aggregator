"""Shared helpers for API routers."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from curanews.api.schemas import ArticleItem
from curanews.db.entity_repository import EntityRepository
from curanews.db.models import Article, Source


def display_source_name(article: Article, source: Source | None) -> str:
    """Prefer publisher metadata (BBC News) over the adapter registry key."""
    meta = article.raw_metadata or {}
    publisher = meta.get("publisher")
    if isinstance(publisher, str) and publisher.strip():
        return publisher.strip()
    domain = meta.get("domain_source")
    if isinstance(domain, str) and ":" in domain:
        label = domain.split(":", 1)[1].strip()
        if label:
            return label
    return source.name if source else "unknown"


def article_to_item(
    session: Session,
    article: Article,
    *,
    score: float | None = None,
    read: bool = False,
    read_at: datetime | None = None,
) -> ArticleItem:
    source = session.get(Source, article.source_id)
    entities = EntityRepository(session).list_for_article(article.id)
    return ArticleItem(
        id=article.id,
        title=article.title,
        summary=article.summary,
        url=article.url,
        source_name=display_source_name(article, source),
        category=article.category,
        published_at=article.published_at,
        entities=[e.label for e in entities],
        score=score,
        read=read,
        read_at=read_at,
    )


def list_articles_query(
    session: Session,
    *,
    limit: int,
    offset: int,
    source: str | None = None,
    q: str | None = None,
) -> tuple[list[Article], int]:
    stmt = select(Article)
    count_base = select(Article)
    if source:
        stmt = stmt.join(Source).where(Source.name == source)
        count_base = count_base.join(Source).where(Source.name == source)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(Article.title.ilike(pattern))
        count_base = count_base.where(Article.title.ilike(pattern))

    rows = list(session.scalars(stmt.order_by(Article.scraped_at.desc()).offset(offset).limit(limit)).all())
    total = len(list(session.scalars(count_base).all()))
    return rows, total
