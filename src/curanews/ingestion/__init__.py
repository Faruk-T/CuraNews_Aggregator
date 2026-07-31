"""Ingestion helpers (clean → dedupe → persist)."""

from curanews.ingestion.cleaning import clean_news_payload, collapse_whitespace

__all__ = ["clean_news_payload", "collapse_whitespace"]
