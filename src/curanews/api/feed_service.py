"""Build personalized feeds with Redis cache (Issue #17 / G17)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from curanews.api.schemas import ArticleItem, FeedResponse
from curanews.api.services import article_to_item
from curanews.cache.feed_cache import CacheOutcome, FeedCache
from curanews.db.models import Article
from curanews.db.user_repository import UserRepository
from curanews.nlp.curation import CurationEngine


def feed_query(*, limit: int) -> dict[str, Any]:
    return {"limit": limit}


def build_feed_response(
    session: Session,
    *,
    user_id: str,
    limit: int,
    cache: FeedCache | None = None,
) -> FeedResponse:
    """Return scored feed; use Redis HIT when possible, else compute + SET."""
    users = UserRepository(session)
    user = users.get_by_external_key(user_id)
    if user is None:
        raise LookupError(f"user {user_id!r} not found — seed demo users")

    query = feed_query(limit=limit)
    feed_cache = cache or FeedCache()
    cached = feed_cache.get(user_id, query)

    if cached.outcome == CacheOutcome.HIT and isinstance(cached.payload, dict):
        payload = dict(cached.payload)
        payload["cache"] = "hit"
        return FeedResponse.model_validate(payload)

    candidates = list(session.scalars(select(Article)).all())
    ranked = CurationEngine(session).rank(user.id, candidates, top_k=limit)
    items: list[ArticleItem] = [
        article_to_item(session, scored.article, score=round(scored.score, 4)) for scored in ranked
    ]
    cache_status = "bypass" if cached.outcome == CacheOutcome.BYPASS else "miss"
    response = FeedResponse(
        user_id=user_id,
        generated_at=datetime.now(timezone.utc),
        cache=cache_status,  # type: ignore[arg-type]
        items=items,
    )
    # Store without forcing cache flag so HIT responses can overwrite to "hit"
    to_store = response.model_dump(mode="json")
    to_store["cache"] = "miss"
    feed_cache.set(user_id, query, to_store)
    return response
