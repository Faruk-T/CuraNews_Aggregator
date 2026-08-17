"""GET /topics — popular entities (Issue #16)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from curanews.api.deps import get_db
from curanews.api.schemas import TopicItem, TopicsResponse
from curanews.db.models import ArticleEntity, Entity

router = APIRouter(tags=["topics"])


@router.get("/topics", response_model=TopicsResponse)
def list_topics(
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_db),
) -> TopicsResponse:
    stmt = (
        select(
            Entity.label,
            Entity.ent_type,
            Entity.normalized,
            func.count(ArticleEntity.article_id).label("article_count"),
        )
        .outerjoin(ArticleEntity, ArticleEntity.entity_id == Entity.id)
        .group_by(Entity.id)
        .order_by(func.count(ArticleEntity.article_id).desc())
        .limit(limit)
    )
    rows = session.execute(stmt).all()
    items = [
        TopicItem(
            label=row.label,
            ent_type=row.ent_type,
            normalized=row.normalized,
            article_count=int(row.article_count or 0),
        )
        for row in rows
    ]
    return TopicsResponse(items=items)
