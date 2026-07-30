"""Scrapy pipelines — validation first to block silent corruption."""

from __future__ import annotations

from itemadapter import ItemAdapter
from scrapy.crawler import Crawler

from curanews.scrapers.validators import IncompleteNewsItemError, assert_news_item_complete


class NewsItemValidationPipeline:
    """Drop / fail incomplete items before any persistence stage."""

    def __init__(self, crawler: Crawler | None = None) -> None:
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> NewsItemValidationPipeline:
        return cls(crawler)

    def process_item(self, item):  # noqa: ANN001
        try:
            assert_news_item_complete(ItemAdapter(item).asdict())
        except IncompleteNewsItemError:
            spider = self.crawler.spider if self.crawler is not None else None
            if spider is not None:
                spider.logger.warning("dropping incomplete item: %s", dict(item))
            raise
        return item
