"""GET /feed — curated ranking with Redis HIT/MISS (Issue #17 / G17)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from curanews.api.auth import get_current_user_optional, resolve_reader
from curanews.api.deps import get_db
from curanews.api.feed_service import ANONYMOUS_CACHE_KEY, build_feed_response
from curanews.api.schemas import FeedResponse
from curanews.cache.feed_cache import FeedCache
from curanews.db.models import User

router = APIRouter(tags=["feed"])


def get_feed_cache() -> FeedCache:
    return FeedCache()


@router.get("/feed", response_model=FeedResponse)
def get_feed(
    response: Response,
    user_id: str | None = Query(default=None, description="Anonymous reader key"),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User | None = Depends(get_current_user_optional),
    session: Session = Depends(get_db),
    cache: FeedCache = Depends(get_feed_cache),
) -> FeedResponse:
    if current_user is None and not user_id:
        reader_key = ANONYMOUS_CACHE_KEY
    else:
        user = resolve_reader(
            session, external_key=user_id, current_user=current_user, create=False
        )
        reader_key = user.external_key if user is not None else str(user_id)
    feed = build_feed_response(session, user_id=reader_key, limit=limit, cache=cache)
    response.headers["X-Cache"] = feed.cache
    return feed
