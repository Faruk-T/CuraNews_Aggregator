"""Unit tests for Scrapy NewsItem + validation helpers."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from curanews.domain import RawArticleDraft
from curanews.scrapers import (
    IncompleteNewsItemError,
    NewsItem,
    assert_news_item_complete,
    news_article_from_item,
    promote_draft,
)


def _complete_item(**overrides) -> NewsItem:
    item = NewsItem(
        article_id=str(uuid4()),
        title="Central bank holds rates",
        url="https://example.com/news/rates",
        content="The central bank kept interest rates unchanged.",
        published_date=datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc),
        source="ExampleNews",
        category="finance",
    )
    for key, value in overrides.items():
        item[key] = value
    return item


def test_assert_complete_item_passes():
    assert_news_item_complete(_complete_item())


def test_assert_complete_item_fails_on_missing_url():
    item = _complete_item()
    del item["url"]
    with pytest.raises(IncompleteNewsItemError, match="url"):
        assert_news_item_complete(item)


def test_news_article_from_item_builds_domain_model():
    article = news_article_from_item(_complete_item())
    assert article.title.startswith("Central bank")
    assert article.source == "ExampleNews"


def test_promote_draft_requires_core_fields():
    draft = RawArticleDraft(title="Only title")
    with pytest.raises(IncompleteNewsItemError):
        promote_draft(draft)


def test_promote_draft_success():
    draft = RawArticleDraft(
        title="Sports final ends in draw",
        url="https://example.com/sports/final",
        content="The match ended 1-1 after extra time.",
        published_date=datetime(2026, 7, 27, 18, 30, tzinfo=timezone.utc),
        source="SportsWire",
        category="sports",
    )
    article = promote_draft(draft)
    assert article.category == "sports"
    assert article.article_id is not None
