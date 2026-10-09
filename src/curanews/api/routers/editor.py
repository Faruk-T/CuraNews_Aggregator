"""Editor desk router for original, in-house articles (Day 22)."""

from __future__ import annotations

import hashlib
import threading
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from curanews.api.auth import require_editor
from curanews.api.deps import get_db
from curanews.api.schemas import ArticleItem, EditorArticleCreate
from curanews.api.services import article_to_item
from curanews.api.urls import article_path, public_base_url, safe_http_url, video_embed_url
from curanews.config import get_settings
from curanews.db.models import Article, Source, User
from curanews.ingestion.scheduler import IngestScheduler
from curanews.nlp.categorizer import (
    calculate_read_time,
    detect_breaking_news,
    normalize_category_name,
)

router = APIRouter(prefix="/editor", tags=["editor"])

EDITORIAL_SOURCE_NAME = "CuraNews Editör Masası"


def _ensure_editorial_source(session: Session, base_url: str) -> Source:
    source = session.query(Source).filter(Source.name == EDITORIAL_SOURCE_NAME).first()
    if not source:
        source = Source(
            name=EDITORIAL_SOURCE_NAME,
            base_url=base_url,
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
    request: Request,
    current_user: User = Depends(require_editor),
    session: Session = Depends(get_db),
) -> ArticleItem:
    image_url = safe_http_url(req.image_url)
    if req.image_url and image_url is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Kapak görseli http(s) ile başlayan geçerli bir adres olmalı.",
        )
    video_url = video_embed_url(req.video_url)
    if req.video_url and video_url is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Video için yalnızca YouTube veya Vimeo bağlantıları kabul edilir.",
        )

    base_url = public_base_url(request)
    source = _ensure_editorial_source(session, base_url)

    canonical_cat = normalize_category_name(req.category) or "gundem"
    read_time = calculate_read_time(req.body, req.summary)
    is_breaking = detect_breaking_news(req.title, req.summary)
    author_name = current_user.full_name or "CuraNews Editörü"

    article_id = uuid.uuid4()
    title = req.title.strip()
    url = f"{base_url}/{article_path(article_id, title)}"
    now = datetime.now(UTC)

    metadata: dict[str, Any] = {
        "provider": "editorial",
        "publisher": EDITORIAL_SOURCE_NAME,
        "is_editorial": True,
        "author_name": author_name,
        "author_title": req.author_title.strip(),
        "author_avatar": current_user.avatar_url,
        "image_url": image_url,
        "video_url": video_url,
        "is_breaking": is_breaking,
        "read_time_minutes": read_time,
        "category_slug": canonical_cat,
    }

    article = Article(
        id=article_id,
        source_id=source.id,
        url=url,
        url_hash=hashlib.sha256(url.encode("utf-8")).hexdigest(),
        title=title,
        summary=req.summary.strip(),
        body=req.body.strip(),
        author_display=author_name,
        published_at=now,
        scraped_at=now,
        content_hash=hashlib.sha256(f"{req.title}{req.body}".encode()).hexdigest(),
        language="tr",
        category=canonical_cat,
        raw_metadata=metadata,
    )
    session.add(article)
    session.commit()
    session.refresh(article)

    return article_to_item(session, article)


@router.post("/ingest")
def trigger_ingest(current_user: User = Depends(require_editor)) -> dict[str, str]:
    """Kick a background RSS refresh without blocking the editor request."""
    del current_user

    def _run() -> None:
        IngestScheduler.from_settings(get_settings()).tick()

    threading.Thread(target=_run, name="rss-refresh-manual", daemon=True).start()
    return {"status": "accepted"}
