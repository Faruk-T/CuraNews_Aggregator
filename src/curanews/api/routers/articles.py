"""GET /articles — list and detail (Issue #16)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from curanews.api.deps import get_db
from curanews.api.schemas import ArticleItem, ArticleListResponse
from curanews.api.services import article_to_item, list_articles_query
from curanews.db.models import Article

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=ArticleListResponse)
def list_articles(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    source: str | None = Query(default=None, description="Filter by source name"),
    q: str | None = Query(default=None, description="Title search"),
    session: Session = Depends(get_db),
) -> ArticleListResponse:
    rows, total = list_articles_query(session, limit=limit, offset=offset, source=source, q=q)
    items = [article_to_item(session, row) for row in rows]
    return ArticleListResponse(total=total, limit=limit, offset=offset, items=items)


@router.get("/{article_id}", response_model=ArticleItem)
def get_article(article_id: UUID, session: Session = Depends(get_db)) -> ArticleItem:
    article = session.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="article not found")
    return article_to_item(session, article)
