"""Ingestion helpers (clean → scrub → dedupe → persist)."""

from curanews.ingestion.cleaning import (
    clean_news_payload,
    clean_raw_draft,
    collapse_whitespace,
    strip_html_tags,
)
from curanews.ingestion.normalize import article_to_persistence_kwargs, default_base_url
from curanews.ingestion.pipeline import IngestionPipeline, IngestionStats

__all__ = [
    "IngestionPipeline",
    "IngestionStats",
    "article_to_persistence_kwargs",
    "clean_news_payload",
    "clean_raw_draft",
    "collapse_whitespace",
    "default_base_url",
    "strip_html_tags",
]
