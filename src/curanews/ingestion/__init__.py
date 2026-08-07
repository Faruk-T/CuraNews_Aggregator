"""Ingestion helpers (clean → dedupe → persist)."""

from curanews.ingestion.cleaning import (
    clean_news_payload,
    clean_raw_draft,
    collapse_whitespace,
    strip_html_tags,
)

__all__ = [
    "clean_news_payload",
    "clean_raw_draft",
    "collapse_whitespace",
    "strip_html_tags",
]
