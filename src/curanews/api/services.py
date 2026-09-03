"""Shared helpers for API routers."""

from __future__ import annotations

import base64
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
    "habertürk": ("#1B365D", "#FFFFFF", "HABERTÜRK"),
    "curanews editör masası": ("#E11D48", "#FFFFFF", "EDİTÖR"),
}

CATEGORY_FALLBACK_IMAGES: dict[str, str] = {
    "ekonomi": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&auto=format&fit=crop",
    "teknoloji": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&auto=format&fit=crop",
    "spor": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800&auto=format&fit=crop",
    "gundem": "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=800&auto=format&fit=crop",
    "saglik": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=800&auto=format&fit=crop",
    "dunya": "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&auto=format&fit=crop",
    "politika": "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=800&auto=format&fit=crop",
}


def _b64_svg(svg_xml: str) -> str:
    encoded = base64.b64encode(svg_xml.strip().encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def get_source_logo_svg(source_name: str) -> str:
    """Generate authentic, base64-encoded SVG brand logo for news publishers."""
    clean = source_name.lower().strip()

    if "cnn" in clean:
        return _b64_svg(
            "<svg xmlns='http://www.w3.org/2000/svg' width='88' height='22' viewBox='0 0 88 22'>"
            "<rect width='88' height='22' rx='4' fill='#CC0000'/>"
            "<text x='28' y='16' fill='#FFFFFF' font-family='Impact,sans-serif' "
            "font-size='14' font-weight='900'>CNN</text>"
            "<line x1='56' y1='4' x2='56' y2='18' "
            "stroke='rgba(255,255,255,0.4)' stroke-width='1.5'/>"
            "<text x='71' y='15' fill='#FFFFFF' font-family='system-ui,sans-serif' "
            "font-size='9' font-weight='800' text-anchor='middle'>TÜRK</text>"
            "</svg>"
        )

    if "trt" in clean:
        return _b64_svg(
            "<svg xmlns='http://www.w3.org/2000/svg' width='82' height='22' viewBox='0 0 82 22'>"
            "<rect width='82' height='22' rx='4' fill='#C8102E'/>"
            "<text x='26' y='16' fill='#FFFFFF' font-family='system-ui,sans-serif' "
            "font-size='13' font-weight='900'>TRT</text>"
            "<text x='62' y='15' fill='#FFFFFF' font-family='system-ui,sans-serif' "
            "font-size='8.5' font-weight='800' text-anchor='middle'>HABER</text>"
            "</svg>"
        )

    if "ntv" in clean:
        return _b64_svg(
            "<svg xmlns='http://www.w3.org/2000/svg' width='58' height='22' viewBox='0 0 58 22'>"
            "<rect width='58' height='22' rx='4' fill='#00A3E0'/>"
            "<text x='50%' y='16' fill='#FFFFFF' font-family='system-ui,sans-serif' "
            "font-size='13' font-weight='900' text-anchor='middle' letter-spacing='1'>NTV</text>"
            "</svg>"
        )

    if "anadolu" in clean or clean == "aa":
        return _b64_svg(
            "<svg xmlns='http://www.w3.org/2000/svg' width='52' height='22' viewBox='0 0 52 22'>"
            "<rect width='52' height='22' rx='4' fill='#003B70'/>"
            "<text x='50%' y='16' fill='#FFFFFF' font-family='system-ui,sans-serif' "
            "font-size='14' font-weight='900' text-anchor='middle' letter-spacing='1'>AA</text>"
            "</svg>"
        )

    if "habertürk" in clean or "haberturk" in clean:
        return _b64_svg(
            "<svg xmlns='http://www.w3.org/2000/svg' width='92' height='22' viewBox='0 0 92 22'>"
            "<rect width='92' height='22' rx='4' fill='#1B365D'/>"
            "<text x='50%' y='15' fill='#FFFFFF' font-family='system-ui,sans-serif' "
            "font-size='10' font-weight='900' text-anchor='middle' "
            "letter-spacing='0.5'>HABERTÜRK</text>"
            "</svg>"
        )

    if "hürriyet" in clean or "hurriyet" in clean:
        return _b64_svg(
            "<svg xmlns='http://www.w3.org/2000/svg' width='82' height='22' viewBox='0 0 82 22'>"
            "<rect width='82' height='22' rx='4' fill='#E53935'/>"
            "<text x='50%' y='15' fill='#FFFFFF' font-family='Georgia,serif' "
            "font-size='10.5' font-weight='900' text-anchor='middle' "
            "letter-spacing='0.5'>HÜRRİYET</text>"
            "</svg>"
        )

    if "milliyet" in clean:
        return _b64_svg(
            "<svg xmlns='http://www.w3.org/2000/svg' width='78' height='22' viewBox='0 0 78 22'>"
            "<rect width='78' height='22' rx='4' fill='#C62828'/>"
            "<text x='50%' y='15' fill='#FFFFFF' font-family='Georgia,serif' "
            "font-size='11' font-weight='900' text-anchor='middle' "
            "letter-spacing='0.5'>MİLLİYET</text>"
            "</svg>"
        )

    if "sözcü" in clean or "sozcu" in clean:
        return _b64_svg(
            "<svg xmlns='http://www.w3.org/2000/svg' width='72' height='22' viewBox='0 0 72 22'>"
            "<rect width='72' height='22' rx='4' fill='#D32F2F'/>"
            "<text x='50%' y='16' fill='#FFFFFF' font-family='system-ui,sans-serif' "
            "font-size='12' font-weight='900' text-anchor='middle' "
            "letter-spacing='0.5'>SÖZCÜ</text>"
            "</svg>"
        )

    if "bbc" in clean:
        return _b64_svg(
            "<svg xmlns='http://www.w3.org/2000/svg' width='70' height='22' viewBox='0 0 70 22'>"
            "<rect x='2' y='2' width='18' height='18' rx='2' fill='#000000'/>"
            "<text x='11' y='16' fill='#FFFFFF' font-family='system-ui,sans-serif' "
            "font-size='12' font-weight='900' text-anchor='middle'>B</text>"
            "<rect x='24' y='2' width='18' height='18' rx='2' fill='#000000'/>"
            "<text x='33' y='16' fill='#FFFFFF' font-family='system-ui,sans-serif' "
            "font-size='12' font-weight='900' text-anchor='middle'>B</text>"
            "<rect x='46' y='2' width='18' height='18' rx='2' fill='#000000'/>"
            "<text x='55' y='16' fill='#FFFFFF' font-family='system-ui,sans-serif' "
            "font-size='12' font-weight='900' text-anchor='middle'>C</text>"
            "</svg>"
        )

    if "curanews" in clean or "editör" in clean:
        return _b64_svg(
            "<svg xmlns='http://www.w3.org/2000/svg' width='92' height='22' viewBox='0 0 92 22'>"
            "<rect width='92' height='22' rx='4' fill='#E11D48'/>"
            "<text x='50%' y='15' fill='#FFFFFF' font-family='system-ui,sans-serif' "
            "font-size='10' font-weight='900' text-anchor='middle' "
            "letter-spacing='0.5'>CURANEWS</text>"
            "</svg>"
        )

    # Dynamic fallback badge
    bg, fg, label = ("#2D3748", "#FFFFFF", source_name[:4].upper())
    for key, (kbg, kfg, klabel) in SOURCE_BRAND_COLORS.items():
        if key in clean or clean in key:
            bg, fg, label = kbg, kfg, klabel
            break

    width = max(38, len(label) * 9 + 14)
    raw = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='22' "
        f"viewBox='0 0 {width} 22'>"
        f"<rect width='{width}' height='22' rx='4' fill='{bg}'/>"
        f"<text x='50%' y='15' fill='{fg}' font-family='system-ui,sans-serif' "
        f"font-size='10' font-weight='800' text-anchor='middle' "
        f"letter-spacing='0.5'>{label}</text></svg>"
    )
    return _b64_svg(raw)


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

    # Image URL from metadata or enclosures with editorial category fallback
    raw_img = meta.get("image_url")
    if raw_img and str(raw_img).strip():
        image_url = str(raw_img).strip()
    else:
        image_url = CATEGORY_FALLBACK_IMAGES.get(
            cat_slug,
            "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=800&auto=format&fit=crop",
        )

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


# Backward compatibility alias
list_articles_query = list_articles
