"""Onedio-style Editor CMS router for manual news entry (Day 22)."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from curanews.api.auth import get_current_user_optional
from curanews.api.deps import get_db
from curanews.api.schemas import ArticleItem, EditorArticleCreate
from curanews.api.services import article_to_item
from curanews.db.models import Article, Source, User
from curanews.nlp.categorizer import (
    calculate_read_time,
    detect_breaking_news,
    normalize_category_name,
)

router = APIRouter(prefix="/editor", tags=["editor"])

EDITORIAL_SOURCE_NAME = "CuraNews Editör Masası"


def _ensure_editorial_source(session: Session) -> Source:
    source = session.query(Source).filter(Source.name == EDITORIAL_SOURCE_NAME).first()
    if not source:
        source = Source(
            name=EDITORIAL_SOURCE_NAME,
            base_url="https://curanews.com/editor",
            kind="editorial",
            enabled=True,
            robots_respected=True,
        )
        session.add(source)
        session.commit()
        session.refresh(source)
    return source


@router.post("/articles", response_model=ArticleItem)
def create_editor_article(
    req: EditorArticleCreate,
    current_user: User | None = Depends(get_current_user_optional),
    session: Session = Depends(get_db),
) -> ArticleItem:
    # Editorial source
    source = _ensure_editorial_source(session)

    # Calculate hashes and metadata
    canonical_cat = normalize_category_name(req.category) or "gundem"
    read_time = calculate_read_time(req.body, req.summary)
    is_breaking = detect_breaking_news(req.title, req.summary)

    author_name = (
        current_user.full_name
        if current_user and current_user.full_name
        else req.author_name
    )
    author_avatar = (
        current_user.avatar_url
        if current_user and current_user.avatar_url
        else req.author_avatar or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"
    )

    now = datetime.now(UTC)
    unique_slug = f"editorial-{uuid.uuid4().hex[:12]}"
    url = f"https://curanews.com/editor/{unique_slug}"
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    content_hash = hashlib.sha256(f"{req.title}{req.body}".encode()).hexdigest()

    metadata: dict[str, Any] = {
        "provider": "editorial",
        "publisher": EDITORIAL_SOURCE_NAME,
        "is_editorial": True,
        "author_name": author_name,
        "author_title": req.author_title,
        "author_avatar": author_avatar,
        "image_url": req.image_url,
        "video_url": req.video_url,
        "is_breaking": is_breaking,
        "read_time_minutes": read_time,
        "category_slug": canonical_cat,
    }

    article = Article(
        source_id=source.id,
        url=url,
        url_hash=url_hash,
        title=req.title.strip(),
        summary=req.summary.strip(),
        body=req.body.strip(),
        author_display=author_name,
        published_at=now,
        scraped_at=now,
        content_hash=content_hash,
        language="tr",
        category=canonical_cat,
        raw_metadata=metadata,
    )
    session.add(article)
    session.commit()
    session.refresh(article)

    item = article_to_item(session, article)
    return item
