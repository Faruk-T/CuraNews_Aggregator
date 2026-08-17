"""GET /feed — personalized ranking (Issue #16 skeleton; G17 deepens cache)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from curanews.api.deps import get_db
from curanews.api.schemas import FeedResponse
from curanews.api.services import article_to_item
from curanews.db.models import Article
from curanews.db.user_repository import UserRepository
from curanews.nlp.curation import CurationEngine

router = APIRouter(tags=["feed"])


@router.get("/feed", response_model=FeedResponse)
def get_feed(
    user_id: str = Query(..., description="User external_key, e.g. demo-user-a"),
    limit: int = Query(default=10, ge=1, le=50),
    session: Session = Depends(get_db),
) -> FeedResponse:
    users = UserRepository(session)
    user = users.get_by_external_key(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"user {user_id!r} not found — seed demo users")

    candidates = list(session.scalars(select(Article)).all())
    ranked = CurationEngine(session).rank(user.id, candidates, top_k=limit)
    items = [
        article_to_item(session, scored.article, score=round(scored.score, 4)) for scored in ranked
    ]
    return FeedResponse(
        user_id=user_id,
        generated_at=datetime.now(timezone.utc),
        cache="miss",
        items=items,
    )
