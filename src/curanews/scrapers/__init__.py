"""Scrapers package — static acquisition (Scrapy / BeautifulSoup)."""

from curanews.scrapers.items import NEWS_ITEM_REQUIRED_FIELDS, NewsItem
from curanews.scrapers.validators import (
    IncompleteNewsItemError,
    assert_news_item_complete,
    news_article_from_item,
    promote_draft,
)

__all__ = [
    "NEWS_ITEM_REQUIRED_FIELDS",
    "NewsItem",
    "IncompleteNewsItemError",
    "assert_news_item_complete",
    "news_article_from_item",
    "promote_draft",
]
