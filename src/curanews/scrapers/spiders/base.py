"""Shared spider helpers for CuraNews Scrapy spiders."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import scrapy

from curanews.scrapers.items import NewsItem


class BaseNewsSpider(scrapy.Spider):
    """Base spider with polite defaults and NewsItem factory helpers."""

    custom_settings: dict = {
        "ROBOTSTXT_OBEY": True,
    }

    source_key: str = "unknown"
    default_category: str = "general"

    def build_news_item(
        self,
        *,
        title: str,
        url: str,
        content: str,
        published_date: datetime | None = None,
        category: str | None = None,
        summary: str | None = None,
        author: str | None = None,
    ) -> NewsItem:
        """Create a complete ``NewsItem`` ready for the validation pipeline."""
        now = datetime.now(timezone.utc)
        return NewsItem(
            article_id=str(uuid4()),
            title=title,
            url=url,
            content=content,
            published_date=published_date or now,
            source=self.source_key,
            category=(category or self.default_category),
            summary=summary,
            author=author,
            scraped_at=now,
            metadata={"spider": self.name},
        )

    @staticmethod
    def path_to_file_url(path: Path) -> str:
        """Convert a local filesystem path to a ``file://`` URL for Scrapy."""
        return path.resolve().as_uri()
