"""Validation helpers that block incomplete news payloads."""

from __future__ import annotations

from typing import Any, Mapping

from curanews.domain.models import REQUIRED_NEWS_FIELDS, NewsArticle, RawArticleDraft
from curanews.scrapers.items import NEWS_ITEM_REQUIRED_FIELDS, NewsItem


class IncompleteNewsItemError(ValueError):
    """Raised when a scrape payload is missing required fields."""


def missing_required_fields(
    payload: Mapping[str, Any],
    required: tuple[str, ...] = REQUIRED_NEWS_FIELDS,
) -> list[str]:
    """Return names of required fields that are missing or empty."""
    missing: list[str] = []
    for name in required:
        value = payload.get(name)
        if value is None:
            missing.append(name)
            continue
        if isinstance(value, str) and not value.strip():
            missing.append(name)
    return missing


def assert_news_item_complete(item: NewsItem | Mapping[str, Any]) -> None:
    """Fail fast on incomplete Scrapy items (anti silent-corruption)."""
    data = dict(item) if not isinstance(item, Mapping) else dict(item)
    missing = missing_required_fields(data, NEWS_ITEM_REQUIRED_FIELDS)
    if missing:
        raise IncompleteNewsItemError(
            f"NewsItem missing required fields: {', '.join(missing)}"
        )


def news_article_from_item(item: NewsItem | Mapping[str, Any]) -> NewsArticle:
    """Validate a Scrapy item / dict and return a ``NewsArticle``."""
    assert_news_item_complete(item)
    data = dict(item) if not isinstance(item, Mapping) else dict(item)
    return NewsArticle.model_validate(data)


def promote_draft(draft: RawArticleDraft, *, article_id: Any | None = None) -> NewsArticle:
    """Promote a loose draft to a strict ``NewsArticle`` or raise."""
    from uuid import uuid4

    payload = draft.model_dump(exclude_none=True)
    payload["article_id"] = article_id if article_id is not None else uuid4()
    # article_id is generated here; other required fields must come from the draft
    required_from_draft = tuple(f for f in REQUIRED_NEWS_FIELDS if f != "article_id")
    missing = missing_required_fields(payload, required_from_draft)
    if missing:
        raise IncompleteNewsItemError(
            f"RawArticleDraft missing required fields: {', '.join(missing)}"
        )
    return NewsArticle.model_validate(payload)
