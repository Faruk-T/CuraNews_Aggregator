"""Shared helpers for API routers."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from curanews.api.schemas import ArticleItem
from curanews.db.entity_repository import EntityRepository
from curanews.db.models import Article, Source
from curanews.nlp.categorizer import (
    calculate_read_time,
    categorize_text,
    detect_breaking_news,
    get_category_display_name,
    normalize_category_name,
)


def display_source_name(article: Article, source: Source | None) -> str:
    """Prefer publisher metadata (BBC News) over the adapter registry key."""
    meta = article.raw_metadata or {}
    publisher = meta.get("publisher")
    if isinstance(publisher, str) and publisher.strip():
        return publisher.strip()
    domain = meta.get("domain_source")
    if isinstance(domain, str) and ":" in domain:
        label = domain.split(":", 1)[1].strip()
        if label:
            return label
    return source.name if source else "unknown"


SOURCE_BRAND_COLORS: dict[str, tuple[str, str, str]] = {
    # name_key: (bg_color, text_color, short_code)
    "anadolu ajansı": ("#003B70", "#FFFFFF", "AA"),
    "trt haber": ("#C8102E", "#FFFFFF", "TRT"),
    "ntv": ("#00A3E0", "#FFFFFF", "NTV"),
    "ntv spor": ("#0288D1", "#FFFFFF", "NTV SPOR"),
    "bbc news": ("#121212", "#FFFFFF", "BBC"),
    "bbc türkçe": ("#BB1919", "#FFFFFF", "BBC"),
    "a haber": ("#00796B", "#FFFFFF", "A HABER"),
    "a haber spor": ("#00897B", "#FFFFFF", "A SPOR"),
    "the guardian": ("#052962", "#FFE500", "GUARDIAN"),
    "al jazeera": ("#E06D00", "#FFFFFF", "AL JAZEERA"),
    "dw türkçe": ("#002D5A", "#FFFFFF", "DW"),
    "npr": ("#0C2340", "#FFFFFF", "NPR"),
    "sözcü": ("#D32F2F", "#FFFFFF", "SÖZCÜ"),
    "hürriyet": ("#E53935", "#FFFFFF", "HÜRRİYET"),
    "cnn türk": ("#CC0000", "#FFFFFF", "CNN"),
    "curanews editör masası": ("#E11D48", "#FFFFFF", "EDİTÖR"),
}


def get_source_logo_svg(source_name: str) -> str:
    """Generate lightweight inline SVG logo badge for news publishers."""
    clean = source_name.lower().strip()
    bg, fg, label = ("#2D3748", "#FFFFFF", source_name[:3].upper())
    for key, (kbg, kfg, klabel) in SOURCE_BRAND_COLORS.items():
        if key in clean or clean in key:
            bg, fg, label = kbg, kfg, klabel
        width = max(36, len(label) * 9 + 14)
    svg_txt = (
        f"data:image/svg+xml;utf8,"
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='22' "
        f"viewBox='0 0 {width} 22'>"
        f"<rect width='{width}' height='22' rx='4' fill='{bg}'/>"
        f"<text x='50%' y='15' fill='{fg}' font-family='system-ui,sans-serif' "
        f"font-size='10' font-weight='800' text-anchor='middle' "
        f"letter-spacing='0.5'>{label}</text></svg>"
    )
    return svg_txt


def article_to_item(
    session: Session,
    article: Article,
    *,
    score: float | None = None,
    read: bool = False,
    read_at: datetime | None = None,
    is_bookmarked: bool = False,
    comments_count: int = 0,
) -> ArticleItem:
    source = session.get(Source, article.source_id)
    entities = EntityRepository(session).list_for_article(article.id)
    source_name = display_source_name(article, source)
    meta = article.raw_metadata or {}

    # Category normalization or AI categorization
    cat_slug = normalize_category_name(article.category)
    if not cat_slug:
        cat_slug, _ = categorize_text(
            article.title,
            summary=article.summary or "",
            body=article.body or "",
            default_category=article.category,
        )
    category_display = get_category_display_name(cat_slug)

    # Image URL from metadata or enclosures
    image_url = meta.get("image_url")
    video_url = meta.get("video_url")
    is_editorial = bool(meta.get("is_editorial"))
    author_title = meta.get("author_title")
    author_avatar = meta.get("author_avatar")

    # Read time & breaking news status
    has_breaking = bool(meta.get("is_breaking"))
    is_breaking = has_breaking or detect_breaking_news(article.title, article.summary or "")
    meta_rt = meta.get("read_time_minutes")
    read_time = int(meta_rt or calculate_read_time(article.body or "", article.summary or ""))

    return ArticleItem(
        id=article.id,
        title=article.title,
        summary=article.summary,
        body=article.body or article.summary,
        url=article.url,
        source_name=source_name,
        source_logo=get_source_logo_svg(source_name),
        image_url=image_url,
        video_url=video_url,
        category=cat_slug,
        category_name=category_display,
        is_breaking=is_breaking,
        read_time_minutes=read_time,
        is_editorial=is_editorial,
        author_display=article.author_display or meta.get("author_name"),
        author_title=author_title,
        author_avatar=author_avatar,
        published_at=article.published_at,
        scraped_at=article.scraped_at,
        score=score,
        read=read,
        read_at=read_at,
        is_bookmarked=is_bookmarked,
        comments_count=comments_count,
        entities=[e.label for e in entities],
    )


def list_articles(
    session: Session,
    *,
    offset: int = 0,
    limit: int = 50,
    source: str | None = None,
    category: str | None = None,
    q: str | None = None,
) -> tuple[list[Article], int]:
    stmt = select(Article)
    count_base = select(Article)
    if source:
        stmt = stmt.join(Source).where(Source.name == source)
        count_base = count_base.join(Source).where(Source.name == source)
    if category:
        stmt = stmt.where(Article.category == category)
        count_base = count_base.where(Article.category == category)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(Article.title.ilike(pattern))
        count_base = count_base.where(Article.title.ilike(pattern))

    ordered_stmt = stmt.order_by(Article.scraped_at.desc()).offset(offset).limit(limit)
    rows = list(session.scalars(ordered_stmt).all())
    total = len(list(session.scalars(count_base).all()))
    return rows, total
