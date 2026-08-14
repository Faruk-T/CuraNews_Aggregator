"""PII scrubbing / pseudonymization (Issue #15 / G15).

Masks emails, phone numbers, and social handles before persistence or display.
"""

from __future__ import annotations

import re

from curanews.domain.models import NewsArticle

_WHITESPACE_RE = re.compile(r"\s+")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(
    r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{2,4}(?!\w)"
)
_HANDLE_RE = re.compile(r"(?<!\w)@[A-Za-z0-9_]{2,32}\b")

EMAIL_REDACTION = "[email-redacted]"
PHONE_REDACTION = "[phone-redacted]"
HANDLE_REDACTION = "[handle-redacted]"


def _collapse_whitespace(value: str) -> str:
    return _WHITESPACE_RE.sub(" ", value).strip()


def scrub_pii(value: str) -> str:
    """Collapse whitespace and mask email, phone, and @handle patterns."""
    cleaned = _collapse_whitespace(value)
    cleaned = _EMAIL_RE.sub(EMAIL_REDACTION, cleaned)
    cleaned = _HANDLE_RE.sub(HANDLE_REDACTION, cleaned)
    cleaned = _PHONE_RE.sub(PHONE_REDACTION, cleaned)
    return cleaned


def scrub_news_article_pii(article: NewsArticle) -> NewsArticle:
    """Return a copy with PII scrubbed from text fields."""
    updates: dict[str, str] = {
        "title": scrub_pii(article.title),
        "content": scrub_pii(article.content),
    }
    if article.summary:
        updates["summary"] = scrub_pii(article.summary)
    if article.author:
        updates["author"] = scrub_pii(article.author)
    return article.model_copy(update=updates)
