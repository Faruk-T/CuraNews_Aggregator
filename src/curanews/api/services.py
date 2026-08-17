"""Shared helpers for API routers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from curanews.db.entity_repository import EntityRepository
from curanews.db.models import Article, Source
from curanews.api.schemas import ArticleItem


def article_to_item(
    session: Session,
    article: Article,
    *,
    score: float | None = None,
) -> ArticleItem:
    source = session.get(Source, article.source_id)
    entities = EntityRepository(session).list_for_article(article.id)
    return ArticleItem(
        id=article.id,
        title=article.title,
        summary=article.summary,
        url=article.url,
        source_name=source.name if source else "unknown",
        category=article.category,
        published_at=article.published_at,
        entities=[e.label for e in entities],
        score=score,
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
