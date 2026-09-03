"""Bookmarks / Favorites router (Day 22)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from curanews.api.auth import get_current_user_optional
from curanews.api.deps import get_db
from curanews.api.schemas import (
    BookmarkListResponse,
    BookmarkToggleRequest,
    BookmarkToggleResponse,
)
from curanews.api.services import article_to_item
from curanews.db.models import Article, User, UserBookmark

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


def _resolve_user(session: Session, user_id_param: str | None, current_user: User | None) -> User:
    if current_user:
        return current_user
    key = user_id_param or "demo-user-a"
    user = session.query(User).filter(User.external_key == key).first()
    if not user:
        user = User(external_key=key)
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


@router.post("", response_model=BookmarkToggleResponse)
def toggle_bookmark(
    req: BookmarkToggleRequest,
    current_user: User | None = Depends(get_current_user_optional),
    session: Session = Depends(get_db),
) -> BookmarkToggleResponse:
    user = _resolve_user(session, req.user_id, current_user)

    existing = (
        session.query(UserBookmark)
        .filter(UserBookmark.user_id == user.id, UserBookmark.article_id == req.article_id)
        .first()
    )

    if existing:
        session.delete(existing)
        session.commit()
        is_bookmarked = False
    else:
        new_bm = UserBookmark(user_id=user.id, article_id=req.article_id)
        session.add(new_bm)
        session.commit()
        is_bookmarked = True

    count_stmt = select(UserBookmark).where(UserBookmark.user_id == user.id)
    total = len(list(session.scalars(count_stmt).all()))
    return BookmarkToggleResponse(
        article_id=req.article_id,
        is_bookmarked=is_bookmarked,
        total_bookmarks=total,
    )


@router.get("", response_model=BookmarkListResponse)
def list_bookmarks(
    user_id: str | None = Query(default=None),
    current_user: User | None = Depends(get_current_user_optional),
    session: Session = Depends(get_db),
) -> BookmarkListResponse:
    user = _resolve_user(session, user_id, current_user)

    bookmarks = list(
        session.scalars(
            select(UserBookmark)
            .where(UserBookmark.user_id == user.id)
            .order_by(UserBookmark.created_at.desc())
        ).all()
    )

    items = []
    for bm in bookmarks:
        article = session.get(Article, bm.article_id)
        if article:
            item = article_to_item(session, article)
            item.is_bookmarked = True
            items.append(item)

    return BookmarkListResponse(total=len(items), items=items)
