"""Bookmarks / Favorites router (Day 22)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from curanews.api.auth import get_current_user_optional, resolve_reader
from curanews.api.deps import get_db
from curanews.api.schemas import (
    BookmarkListResponse,
    BookmarkToggleRequest,
    BookmarkToggleResponse,
)
from curanews.api.services import article_to_item
from curanews.db.models import Article, User, UserBookmark

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.post("", response_model=BookmarkToggleResponse)
def toggle_bookmark(
    req: BookmarkToggleRequest,
    current_user: User | None = Depends(get_current_user_optional),
    session: Session = Depends(get_db),
) -> BookmarkToggleResponse:
    user = resolve_reader(session, external_key=req.user_id, current_user=current_user, create=True)
    assert user is not None
    if session.get(Article, req.article_id) is None:
        raise HTTPException(status_code=404, detail="Haber bulunamadı.")

    existing = (
        session.query(UserBookmark)
        .filter(UserBookmark.user_id == user.id, UserBookmark.article_id == req.article_id)
        .first()
    )
    if existing:
        session.delete(existing)
        is_bookmarked = False
    else:
        session.add(UserBookmark(user_id=user.id, article_id=req.article_id))
        is_bookmarked = True
    session.commit()

    total = session.scalar(
        select(func.count()).select_from(UserBookmark).where(UserBookmark.user_id == user.id)
    )
    return BookmarkToggleResponse(
        article_id=req.article_id,
        is_bookmarked=is_bookmarked,
        total_bookmarks=int(total or 0),
    )


@router.get("", response_model=BookmarkListResponse)
def list_bookmarks(
    user_id: str | None = Query(default=None),
    current_user: User | None = Depends(get_current_user_optional),
    session: Session = Depends(get_db),
) -> BookmarkListResponse:
    user = resolve_reader(session, external_key=user_id, current_user=current_user, create=False)
    if user is None:
        return BookmarkListResponse(total=0, items=[])

    bookmarks = session.scalars(
        select(UserBookmark)
        .where(UserBookmark.user_id == user.id)
        .order_by(UserBookmark.created_at.desc())
        .limit(200)
    ).all()

    items = []
    for bm in bookmarks:
        article = session.get(Article, bm.article_id)
        if article:
            items.append(article_to_item(session, article, is_bookmarked=True))

    return BookmarkListResponse(total=len(items), items=items)
