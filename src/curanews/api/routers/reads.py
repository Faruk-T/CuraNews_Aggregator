"""POST /reads — mark article as read (Issue #16)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from curanews.api.deps import get_db
from curanews.api.schemas import ReadCreate, ReadResponse
from curanews.db.models import Article
from curanews.db.user_repository import UserRepository

router = APIRouter(tags=["reads"])


@router.post("/reads", response_model=ReadResponse, status_code=201)
def create_read(payload: ReadCreate, session: Session = Depends(get_db)) -> ReadResponse:
    users = UserRepository(session)
    user = users.ensure_user(payload.user_id)
    article = session.get(Article, payload.article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="article not found")

    row = users.record_read(user.id, article.id, dwell_ms=payload.dwell_ms)
    return ReadResponse(
        user_id=payload.user_id,
        article_id=payload.article_id,
        read_at=row.read_at,
        dwell_ms=row.dwell_ms,
    )
