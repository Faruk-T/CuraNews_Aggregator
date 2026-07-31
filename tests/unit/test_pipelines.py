"""Tests for Scrapy post-processing pipelines (Issue #5)."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from scrapy.exceptions import DropItem

from curanews.db import SqliteArticleStore
from curanews.scrapers.items import NewsItem
from curanews.scrapers.pipelines import (
    NewsItemCleaningPipeline,
    NewsItemDeduplicationPipeline,
    NewsItemValidationPipeline,
    SqlitePersistPipeline,
)


def _item(**overrides) -> NewsItem:
    base = dict(
        article_id=str(uuid4()),
        title="  Championship   Final  ",
        url="https://example.com/news/final",
        content="  The match ended 1-1.  ",
        published_date=datetime(2026, 7, 30, 18, 0, tzinfo=timezone.utc),
        source="ExampleNews",
        category="Sports",
        summary="The match ended 1-1.",
        metadata={"spider": "example_news"},
    )
    base.update(overrides)
    return NewsItem(**base)


def test_cleaning_pipeline_normalizes_fields():
    pipe = NewsItemCleaningPipeline()
    item = pipe.process_item(_item())
    assert item["title"] == "Championship Final"
    assert item["category"] == "sports"


def test_validation_pipeline_drops_incomplete():
    pipe = NewsItemValidationPipeline()
    item = _item()
    del item["url"]
    with pytest.raises(DropItem):
        pipe.process_item(item)


def test_dedupe_and_persist_pipelines(tmp_path):
    store = SqliteArticleStore(tmp_path / "pipe.sqlite3")
    dedupe = NewsItemDeduplicationPipeline(store)
    # Minimal crawler stub for persist close path is not needed in process_item
    class _Crawler:
        curanews_sqlite_store = store

    persist = SqlitePersistPipeline(_Crawler(), store)

    first = _item()
    assert dedupe.process_item(first) is first
    assert persist.process_item(first) is first
    assert store.count() == 1

    duplicate = _item(article_id=str(uuid4()), title="Other title same url")
    with pytest.raises(DropItem, match="duplicate"):
        dedupe.process_item(duplicate)

    store.close()
