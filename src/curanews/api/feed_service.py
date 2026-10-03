"""Build personalized feeds with Redis cache (Issue #17 / G17)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from curanews.api.schemas import ArticleItem, FeedResponse
from curanews.api.services import article_to_item
from curanews.cache.feed_cache import CacheOutcome, FeedCache
from curanews.config import get_settings
from curanews.db.models import Article
from curanews.db.user_repository import UserRepository
from curanews.nlp.curation import CurationEngine

ANONYMOUS_PROFILE_ID = UUID(int=0)
ANONYMOUS_CACHE_KEY = "__anonymous__"
MAX_FEED_CANDIDATES = 600


def feed_query(*, limit: int) -> dict[str, Any]:
    return {"limit": limit}


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def still_on_main_feed(
    read_at: datetime | None,
    *,
    now: datetime,
    grace_seconds: int,
) -> bool:
    """Unread items stay on Akış; read items stay until the grace window elapses."""
    if read_at is None:
        return True
    return _aware(now) - _aware(read_at) <= timedelta(seconds=grace_seconds)


def build_feed_response(
    session: Session,
    *,
    user_id: str,
    limit: int,
    cache: FeedCache | None = None,
    now: datetime | None = None,
) -> FeedResponse:
    """Return scored feed; use Redis HIT when possible, else compute + SET."""
    users = UserRepository(session)
    user = users.get_by_external_key(user_id)
    profile_id = user.id if user is not None else ANONYMOUS_PROFILE_ID
    # Readers without history share one cached ranking.
    cache_key = user_id if user is not None else ANONYMOUS_CACHE_KEY

    query = feed_query(limit=limit)
    feed_cache = cache or FeedCache()
    cached = feed_cache.get(cache_key, query)

    if cached.outcome == CacheOutcome.HIT and isinstance(cached.payload, dict):
        payload = dict(cached.payload)
        payload["cache"] = "hit"
        payload["user_id"] = user_id
        return FeedResponse.model_validate(payload)

    clock = now or datetime.now(UTC)
    grace_seconds = get_settings().read_inbox_grace_seconds
    read_times = users.read_times(user.id) if user is not None else {}
    stale_ids = {
        article_id
        for article_id, read_at in read_times.items()
        if not still_on_main_feed(read_at, now=clock, grace_seconds=grace_seconds)
    }

    candidates = list(
        session.scalars(
            select(Article)
            .order_by(Article.published_at.desc().nulls_last())
            .limit(MAX_FEED_CANDIDATES)
        ).all()
    )
    inbox_candidates = [article for article in candidates if article.id not in stale_ids]

    ranked = CurationEngine(session).rank(
        profile_id, inbox_candidates, top_k=limit, hide_read=False, now=clock
    )
    items: list[ArticleItem] = [
        article_to_item(
            session,
            scored.article,
            score=round(scored.score, 4),
            read=scored.article.id in read_times,
            read_at=read_times.get(scored.article.id),
        )
        for scored in ranked
    ]
    read_items = _read_archive(session, read_times=read_times, limit=limit)
    cache_status = "bypass" if cached.outcome == CacheOutcome.BYPASS else "miss"
    response = FeedResponse(
        user_id=user_id,
        generated_at=clock,
        cache=cache_status,  # type: ignore[arg-type]
        items=items,
        read_items=read_items,
        inbox_grace_seconds=grace_seconds,
    )
    # Store without forcing cache flag so HIT responses can overwrite to "hit"
    to_store = response.model_dump(mode="json")
    to_store["cache"] = "miss"
    feed_cache.set(cache_key, query, to_store)
    return response


def _read_archive(
    session: Session,
    *,
    read_times: dict[UUID, datetime],
    limit: int,
) -> list[ArticleItem]:
    """Okunanlar tab: all marked-read articles, newest first (grace does not apply)."""
    if not read_times:
        return []
    newest_ids = sorted(read_times, key=lambda aid: _aware(read_times[aid]), reverse=True)
    articles = session.scalars(select(Article).where(Article.id.in_(newest_ids[:limit]))).all()
    ordered = sorted(
        articles,
        key=lambda article: _aware(read_times[article.id]),
        reverse=True,
    )
    return [
        article_to_item(
            session,
            article,
            read=True,
            read_at=read_times[article.id],
        )
        for article in ordered[:limit]
    ]
