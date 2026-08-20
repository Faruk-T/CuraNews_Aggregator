"""Map domain articles to persistence fields."""

from __future__ import annotations

from typing import Any

from curanews.domain.models import NewsArticle
from curanews.scrapers.adapters.base import SourceAdapter

DEFAULT_SOURCE_BASE_URLS: dict[str, str] = {
    "example_news": "https://example.com/",
    "dynamic_demo": "file://fixtures/dynamic_news_scroll.html",
    "gnews_api": "https://gnews.io/api/v4/top-headlines",
    "rss_catalog": "https://feeds.bbci.co.uk/news/world/rss.xml",
}


def default_base_url(adapter: SourceAdapter) -> str:
    """Resolve a registry base URL for ``ensure_source``."""
    return DEFAULT_SOURCE_BASE_URLS.get(adapter.source_id, f"https://{adapter.source_id}/")


def article_to_persistence_kwargs(article: NewsArticle) -> dict[str, Any]:
    """Convert a validated ``NewsArticle`` into repository insert kwargs."""
    metadata = dict(article.metadata)
    metadata.setdefault("domain_source", article.source)
    return {
        "title": article.title,
        "url": str(article.url),
        "body": article.content,
        "summary": article.summary,
        "author_display": article.author,
        "published_at": article.published_date,
        "language": article.language,
        "category": article.category,
        "raw_metadata": metadata,
        "article_id": article.article_id,
    }
