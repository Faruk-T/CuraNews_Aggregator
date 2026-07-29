"""Scrapy pipelines — validation first to block silent corruption."""

from __future__ import annotations

from itemadapter import ItemAdapter

from curanews.scrapers.validators import IncompleteNewsItemError, assert_news_item_complete


class NewsItemValidationPipeline:
    """Drop / fail incomplete items before any persistence stage."""

    def process_item(self, item, spider):  # noqa: ANN001
        try:
            assert_news_item_complete(ItemAdapter(item).asdict())
        except IncompleteNewsItemError:
            spider.logger.warning("dropping incomplete item: %s", dict(item))
            raise
        return item
