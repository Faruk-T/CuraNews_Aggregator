"""Scrapy Item schema for crawled news (Issue #3).

Mandatory fields:
``article_id``, ``title``, ``url``, ``content``, ``published_date``,
``source``, ``category``.
"""

from __future__ import annotations

import scrapy


class NewsItem(scrapy.Item):
    """Scrapy item mirroring the canonical news schema.

    Pipelines should reject items missing any required field instead of
    silently writing incomplete rows.
    """

    article_id = scrapy.Field()
    title = scrapy.Field()
    url = scrapy.Field()
    content = scrapy.Field()
    published_date = scrapy.Field()
    source = scrapy.Field()
    category = scrapy.Field()

    # Optional enrichment fields (filled in later pipeline stages)
    summary = scrapy.Field()
    author = scrapy.Field()
    language = scrapy.Field()
    scraped_at = scrapy.Field()
    metadata = scrapy.Field()


NEWS_ITEM_REQUIRED_FIELDS: tuple[str, ...] = (
    "article_id",
    "title",
    "url",
    "content",
    "published_date",
    "source",
    "category",
)
