"""Comments router for in-site articles (Day 22)."""

from __future__ import annotations

import threading
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from curanews.api.auth import get_current_user_required
from curanews.api.deps import get_db
from curanews.api.ratelimit import comment_limiter, enforce, like_limiter
from curanews.api.schemas import (
    CommentCreate,
    CommentItem,
    CommentLikeResponse,
    CommentListResponse,
)
from curanews.cache.redis_client import get_redis_client
from curanews.db.models import Article, Comment, User

router = APIRouter(tags=["comments"])

_LIKE_TTL_SECONDS = 60 * 60 * 24 * 365
_local_likes: set[str] = set()
_local_likes_lock = threading.Lock()


def _first_like(comment_id: UUID, user_id: UUID) -> bool:
    """True once per (comment, user); Redis-backed with an in-process fallback."""
    key = f"comment_like:{comment_id}:{user_id}"
    client = get_redis_client()
    if client.available:
        return client.set(key, "1", nx=True, ex=_LIKE_TTL_SECONDS)
    with _local_likes_lock:
        if key in _local_likes:
            return False
        if len(_local_likes) > 100_000:
            _local_likes.clear()
        _local_likes.add(key)
        return True


def _to_item(comment: Comment) -> CommentItem:
    return CommentItem(
        id=comment.id,
        article_id=comment.article_id,
        author_name=comment.author_name,
        author_avatar=comment.author_avatar,
        content=comment.content,
        likes=comment.likes,
        created_at=comment.created_at,
    )


@router.get("/articles/{article_id}/comments", response_model=CommentListResponse)
def list_article_comments(
    article_id: UUID, session: Session = Depends(get_db)
) -> CommentListResponse:
    article = session.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Haber bulunamadı.")

    stmt = (
        select(Comment)
        .where(Comment.article_id == article_id)
        .order_by(Comment.created_at.desc())
        .limit(200)
    )
    items = [_to_item(c) for c in session.scalars(stmt).all()]
    return CommentListResponse(article_id=article_id, total=len(items), items=items)


@router.post("/articles/{article_id}/comments", response_model=CommentItem)
def create_article_comment(
    article_id: UUID,
    req: CommentCreate,
    current_user: User = Depends(get_current_user_required),
    session: Session = Depends(get_db),
) -> CommentItem:
    enforce(comment_limiter, str(current_user.id))
    article = session.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Haber bulunamadı.")

    content = req.content.strip()
    if len(content) < 2:
        raise HTTPException(status_code=422, detail="Yorum çok kısa.")

    comment = Comment(
        article_id=article_id,
        user_id=current_user.id,
        author_name=(current_user.full_name or "Okur").strip()[:120],
        author_avatar=current_user.avatar_url,
        content=content,
        likes=0,
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return _to_item(comment)


@router.post("/comments/{comment_id}/like", response_model=CommentLikeResponse)
def like_comment(
    comment_id: UUID,
    current_user: User = Depends(get_current_user_required),
    session: Session = Depends(get_db),
) -> CommentLikeResponse:
    enforce(like_limiter, str(current_user.id))
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Yorum bulunamadı.")

    if _first_like(comment.id, current_user.id):
        comment.likes += 1
        session.commit()
        session.refresh(comment)

    return CommentLikeResponse(comment_id=comment.id, likes=comment.likes)
