"""Lightweight text scrubbing before persistence (Issue #13; expanded in G15)."""

from __future__ import annotations

from curanews.domain.models import NewsArticle
from curanews.privacy.pii import scrub_news_article_pii, scrub_pii


def scrub_text(value: str) -> str:
    """Normalize whitespace and mask PII (email / phone / handle)."""
    return scrub_pii(value)


def scrub_news_article(article: NewsArticle) -> NewsArticle:
    """Return a copy with scrubbed text fields ready for PostgreSQL."""
    return scrub_news_article_pii(article)
