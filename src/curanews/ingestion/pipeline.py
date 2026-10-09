"""Adapter → PostgreSQL ingestion pipeline (Issue #13 / G13)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from curanews.cache.feed_cache import FeedCache
from curanews.db.models import Article
from curanews.db.repository import ArticleRepository, SourceRepository
from curanews.ingestion.cleaning import clean_raw_draft
from curanews.ingestion.normalize import article_to_persistence_kwargs, default_base_url
from curanews.privacy.scrub import scrub_news_article
from curanews.scrapers.adapters.base import SourceAdapter
from curanews.scrapers.validators import IncompleteNewsItemError, promote_draft

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IngestionStats:
    fetched: int = 0
    promoted: int = 0
    inserted: int = 0
    duplicates: int = 0
    skipped_invalid: int = 0
    failed: int = 0
    feed_keys_invalidated: int = 0
    entities_linked: int = 0

    @property
    def persisted(self) -> int:
        return self.inserted + self.duplicates


@dataclass(slots=True)
class IngestionPipeline:
    """Normalize adapter drafts and upsert articles into PostgreSQL."""

    session: Session
    invalidate_feed_cache: bool = True
    run_nlp: bool = True
    commit_every: int | None = None
    _sources: SourceRepository = field(init=False)
    _articles: ArticleRepository = field(init=False)
    _feed_cache: FeedCache | None = field(init=False)

    def __post_init__(self) -> None:
        self._sources = SourceRepository(self.session)
        self._articles = ArticleRepository(self.session)
        self._feed_cache = FeedCache() if self.invalidate_feed_cache else None

    def ingest_adapter(self, adapter: SourceAdapter, *, limit: int = 50) -> IngestionStats:
        stats = IngestionStats()
        source = self._sources.ensure_source(
            name=adapter.source_id,
            base_url=default_base_url(adapter),
            kind=adapter.kind,
        )

        for draft in adapter.fetch(limit=limit):
            stats.fetched += 1
            try:
                article = scrub_news_article(promote_draft(clean_raw_draft(draft)))
                stats.promoted += 1
            except IncompleteNewsItemError as exc:
                stats.skipped_invalid += 1
                logger.info(
                    "ingestion skipped source=%s reason=invalid_draft detail=%s",
                    adapter.source_id,
                    exc,
                )
                continue

            try:
                with self.session.begin_nested():
                    row = self._articles.insert_article(
                        source=source, **article_to_persistence_kwargs(article)
                    )
                    linked = self._tag(row) if row is not None else 0
            except Exception:  # noqa: BLE001
                stats.failed += 1
                logger.exception(
                    "ingestion failed source=%s url=%s", adapter.source_id, article.url
                )
                continue

            if row is None:
                stats.duplicates += 1
                logger.debug("ingestion duplicate source=%s url=%s", adapter.source_id, article.url)
                continue

            stats.inserted += 1
            stats.entities_linked += linked
            logger.info("ingestion inserted source=%s article_id=%s", adapter.source_id, row.id)
            if self.commit_every and stats.inserted % self.commit_every == 0:
                self.session.commit()

        if stats.inserted and self._feed_cache is not None:
            stats.feed_keys_invalidated = self._feed_cache.invalidate_all()

        return stats

    def _tag(self, row: Article) -> int:
        if not self.run_nlp:
            return 0
        from curanews.nlp.tagging import tag_article

        return tag_article(self.session, row)
