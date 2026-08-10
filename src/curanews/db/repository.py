"""Insert and query articles by canonical URL hash."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from curanews.db.models import Article, Source
from curanews.db.sqlite_store import canonical_url_hash


def content_hash(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


class ArticleRepository:
    """Insert and query articles by canonical URL hash."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_url_hash(self, url_hash: str) -> Article | None:
        stmt = select(Article).where(Article.url_hash == url_hash)
        return self._session.scalars(stmt).one_or_none()

    def insert_article(
        self,
        *,
        source: Source,
        title: str,
        url: str,
        body: str | None = None,
        summary: str | None = None,
        author_display: str | None = None,
        published_at: datetime | None = None,
        language: str | None = None,
        category: str | None = None,
        raw_metadata: dict[str, Any] | None = None,
        article_id: UUID | None = None,
    ) -> Article | None:
        """Insert when ``url_hash`` is new; return None on duplicate."""
        url_hash = canonical_url_hash(url)
        if self.get_by_url_hash(url_hash) is not None:
            return None

        body_text = body or summary or title
        row = Article(
            id=article_id,
            source_id=source.id,
            url=url.strip(),
            url_hash=url_hash,
            title=title.strip(),
            summary=summary,
            body=body_text,
            author_display=author_display,
            published_at=published_at,
            scraped_at=datetime.now(timezone.utc),
            content_hash=content_hash(body_text),
            language=language,
            category=category,
            raw_metadata=raw_metadata or {},
        )
        self._session.add(row)
        self._session.flush()
        return row

    def count_articles(self) -> int:
        return int(self._session.scalar(select(func.count()).select_from(Article)) or 0)


class SourceRepository:
    """Lookup and seed crawl sources."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_name(self, name: str) -> Source | None:
        stmt = select(Source).where(Source.name == name)
        return self._session.scalars(stmt).one_or_none()

    def ensure_source(
        self,
        *,
        name: str,
        base_url: str,
        kind: str,
        enabled: bool = True,
        robots_respected: bool = True,
    ) -> Source:
        existing = self.get_by_name(name)
        if existing is not None:
            return existing
        row = Source(
            name=name,
            base_url=base_url,
            kind=kind,
            enabled=enabled,
            robots_respected=robots_respected,
        )
        self._session.add(row)
        self._session.flush()
        return row
