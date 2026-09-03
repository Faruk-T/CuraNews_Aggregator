"""Enrich existing articles with AI categories, breaking flags, and reading times."""

from __future__ import annotations

from curanews.db.models import Article
from curanews.db.session import get_session_factory
from curanews.nlp.categorizer import (
    calculate_read_time,
    categorize_text,
    detect_breaking_news,
    normalize_category_name,
)


def enrich() -> None:
    factory = get_session_factory()
    session = factory()
    try:
        articles = session.query(Article).all()
        updated = 0
        for a in articles:
            dirty = False
            meta = dict(a.raw_metadata or {})
            cat_norm = normalize_category_name(a.category)
            if not cat_norm or cat_norm in {"gundem", "world", "general", "turkey"}:
                cat_slug, conf = categorize_text(
                    a.title,
                    summary=a.summary or "",
                    body=a.body or "",
                    default_category=a.category,
                )
            else:
                cat_slug = cat_norm

            if a.category != cat_slug:
                a.category = cat_slug
                meta["category_slug"] = cat_slug
                dirty = True

            breaking = detect_breaking_news(a.title, a.summary or "")
            if meta.get("is_breaking") != breaking:
                meta["is_breaking"] = breaking
                dirty = True

            read_time = calculate_read_time(a.body or "", a.summary or "")
            if meta.get("read_time_minutes") != read_time:
                meta["read_time_minutes"] = read_time
                dirty = True

            if dirty:
                a.raw_metadata = meta
                updated += 1

        session.commit()
        print(f"Successfully enriched {updated} / {len(articles)} articles!")
    finally:
        session.close()


if __name__ == "__main__":
    enrich()
