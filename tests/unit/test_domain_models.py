"""Unit tests for domain NewsArticle model."""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from curanews.domain import REQUIRED_NEWS_FIELDS, NewsArticle


def _valid_payload(**overrides):
    base = {
        "title": "Markets rally on rate cut hopes",
        "url": "https://example.com/news/markets-rally",
        "content": "Stocks rose after investors priced in a rate cut.",
        "published_date": datetime(2026, 7, 29, 9, 0, tzinfo=timezone.utc),
        "source": "ExampleNews",
        "category": "Economy",
    }
    base.update(overrides)
    return base


def test_required_fields_constant_matches_issue_3():
    assert set(REQUIRED_NEWS_FIELDS) == {
        "article_id",
        "title",
        "url",
        "content",
        "published_date",
        "source",
        "category",
    }


def test_news_article_accepts_valid_payload():
    article = NewsArticle.model_validate(_valid_payload())
    assert isinstance(article.article_id, UUID)
    assert article.category == "economy"
    assert str(article.url).startswith("https://example.com/")


def test_news_article_rejects_blank_title():
    with pytest.raises(ValidationError):
        NewsArticle.model_validate(_valid_payload(title="   "))


def test_news_article_rejects_missing_content():
    payload = _valid_payload()
    del payload["content"]
    with pytest.raises(ValidationError):
        NewsArticle.model_validate(payload)
