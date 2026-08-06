"""Shared ingestion consumer for every ``SourceAdapter`` (Issue #8 / G8)."""

from __future__ import annotations

from curanews.domain.models import NewsArticle
from curanews.scrapers.adapters.base import SourceAdapter
from curanews.scrapers.validators import IncompleteNewsItemError, promote_draft


def ingest_from_adapter(
    adapter: SourceAdapter,
    *,
    limit: int = 50,
) -> list[NewsArticle]:
    """Promote drafts from any adapter through the same validation path."""
    articles: list[NewsArticle] = []
    for draft in adapter.fetch(limit=limit):
        try:
            articles.append(promote_draft(draft))
        except IncompleteNewsItemError:
            continue
    return articles
