"""GET /feed — curated ranking with Redis HIT/MISS (Issue #17 / G17)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from curanews.api.deps import get_db
from curanews.api.feed_service import build_feed_response
from curanews.api.schemas import FeedResponse
from curanews.cache.feed_cache import FeedCache

router = APIRouter(tags=["feed"])


def get_feed_cache() -> FeedCache:
    return FeedCache()


@router.get("/feed", response_model=FeedResponse)
def get_feed(
    response: Response,
    user_id: str = Query(..., description="User external_key, e.g. demo-user-a"),
    limit: int = Query(default=10, ge=1, le=50),
    session: Session = Depends(get_db),
    cache: FeedCache = Depends(get_feed_cache),
) -> FeedResponse:
    try:
        feed = build_feed_response(session, user_id=user_id, limit=limit, cache=cache)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    response.headers["X-Cache"] = feed.cache
    return feed
