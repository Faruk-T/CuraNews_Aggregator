"""Scrapy item pipelines: clean → validate → dedupe → SQLite (Issue #5)."""

from __future__ import annotations

from itemadapter import ItemAdapter
from scrapy.crawler import Crawler
from scrapy.exceptions import DropItem

from curanews.db.sqlite_store import SqliteArticleStore, canonical_url_hash
from curanews.ingestion.cleaning import clean_news_payload
from curanews.scrapers.validators import IncompleteNewsItemError, assert_news_item_complete


def _get_store(crawler: Crawler) -> SqliteArticleStore:
    """Reuse one SQLite store per crawl on the crawler object."""
    store = getattr(crawler, "curanews_sqlite_store", None)
    if store is None:
        path = crawler.settings.get("SQLITE_PATH", "data/local/curanews.sqlite3")
        store = SqliteArticleStore(path)
        crawler.curanews_sqlite_store = store  # type: ignore[attr-defined]
    return store


class NewsItemCleaningPipeline:
    """Normalize whitespace and category formatting before validation."""

    def process_item(self, item):  # noqa: ANN001
        adapter = ItemAdapter(item)
        cleaned = clean_news_payload(adapter.asdict())
        for key, value in cleaned.items():
            adapter[key] = value
        return item


class NewsItemValidationPipeline:
    """Drop incomplete items before persistence (anti silent-corruption)."""

    def __init__(self, crawler: Crawler | None = None) -> None:
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> NewsItemValidationPipeline:
        return cls(crawler)

    def process_item(self, item):  # noqa: ANN001
        try:
            assert_news_item_complete(ItemAdapter(item).asdict())
        except IncompleteNewsItemError as exc:
            spider = self.crawler.spider if self.crawler is not None else None
            if spider is not None:
                spider.logger.warning("dropping incomplete item: %s", exc)
            raise DropItem(str(exc)) from exc
        return item


class NewsItemDeduplicationPipeline:
    """Skip items whose canonical URL hash already exists in SQLite."""

    def __init__(self, store: SqliteArticleStore) -> None:
        self.store = store
        self._seen_in_crawl: set[str] = set()

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> NewsItemDeduplicationPipeline:
        return cls(_get_store(crawler))

    def process_item(self, item):  # noqa: ANN001
        adapter = ItemAdapter(item)
        url = str(adapter.get("url") or "")
        url_hash = canonical_url_hash(url)
        if url_hash in self._seen_in_crawl or self.store.exists_url_hash(url_hash):
            raise DropItem(f"duplicate url hash: {url_hash[:12]}...")
        self._seen_in_crawl.add(url_hash)
        metadata = adapter.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}
        adapter["metadata"] = {**metadata, "url_hash": url_hash}
        return item


class SqlitePersistPipeline:
    """Persist cleaned, unique NewsItems into SQLite."""

    def __init__(self, crawler: Crawler, store: SqliteArticleStore) -> None:
        self.crawler = crawler
        self.store = store
        self.inserted = 0
        self.skipped = 0

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> SqlitePersistPipeline:
        return cls(crawler, _get_store(crawler))

    def close_spider(self, *_args, **_kwargs) -> None:
        spider = self.crawler.spider
        try:
            total_rows = self.store.count()
        except Exception:  # noqa: BLE001
            total_rows = -1
        spider.logger.info(
            "sqlite persist summary inserted=%s skipped=%s total_rows=%s path=%s",
            self.inserted,
            self.skipped,
            total_rows,
            self.store.path,
        )
        if getattr(self.crawler, "curanews_sqlite_store", None) is not None:
            self.store.close()
            self.crawler.curanews_sqlite_store = None  # type: ignore[attr-defined]

    def process_item(self, item):  # noqa: ANN001
        payload = ItemAdapter(item).asdict()
        if self.store.insert_article(payload):
            self.inserted += 1
        else:
            self.skipped += 1
            raise DropItem(f"sqlite duplicate for url={payload.get('url')}")
        return item
