"""Comments router for in-site articles (Day 22)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from curanews.api.auth import get_current_user_optional
from curanews.api.deps import get_db
from curanews.api.schemas import (
    CommentCreate,
    CommentItem,
    CommentLikeResponse,
    CommentListResponse,
)
from curanews.db.models import Article, Comment, User

router = APIRouter(tags=["comments"])


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
    )
    rows = list(session.scalars(stmt).all())

    items = [
        CommentItem(
            id=c.id,
            article_id=c.article_id,
            author_name=c.author_name,
            author_avatar=c.author_avatar,
            content=c.content,
            likes=c.likes,
            created_at=c.created_at,
        )
        for c in rows
    ]
    return CommentListResponse(article_id=article_id, total=len(items), items=items)


@router.post("/articles/{article_id}/comments", response_model=CommentItem)
def create_article_comment(
    article_id: UUID,
    req: CommentCreate,
    current_user: User | None = Depends(get_current_user_optional),
    session: Session = Depends(get_db),
) -> CommentItem:
    article = session.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Haber bulunamadı.")

    user_id = current_user.id if current_user else None
    author_name = (
        current_user.full_name
        if current_user and current_user.full_name
        else req.author_name or "Misafir Okur"
    )
    author_avatar = current_user.avatar_url if current_user else req.author_avatar

    comment = Comment(
        article_id=article_id,
        user_id=user_id,
        author_name=author_name.strip(),
        author_avatar=author_avatar,
        content=req.content.strip(),
        likes=0,
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)

    return CommentItem(
        id=comment.id,
        article_id=comment.article_id,
        author_name=comment.author_name,
        author_avatar=comment.author_avatar,
        content=comment.content,
        likes=comment.likes,
        created_at=comment.created_at,
    )


@router.post("/comments/{comment_id}/like", response_model=CommentLikeResponse)
def like_comment(comment_id: UUID, session: Session = Depends(get_db)) -> CommentLikeResponse:
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Yorum bulunamadı.")

    comment.likes += 1
    session.commit()
    session.refresh(comment)

    return CommentLikeResponse(comment_id=comment.id, likes=comment.likes)
