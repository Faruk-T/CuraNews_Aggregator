"""Lightweight text scrubbing before persistence (Issue #13; expanded in G15)."""

from __future__ import annotations

import re

from curanews.domain.models import NewsArticle
from curanews.ingestion.cleaning import collapse_whitespace

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def scrub_text(value: str) -> str:
    """Normalize whitespace and mask obvious email addresses."""
    cleaned = collapse_whitespace(value)
    return _EMAIL_RE.sub("[email-redacted]", cleaned)


def scrub_news_article(article: NewsArticle) -> NewsArticle:
    """Return a copy with scrubbed text fields ready for PostgreSQL."""
    updates = {
        "title": scrub_text(article.title),
        "content": scrub_text(article.content),
    }
    if article.summary:
        updates["summary"] = scrub_text(article.summary)
    if article.author:
        updates["author"] = scrub_text(article.author)
    return article.model_copy(update=updates)
