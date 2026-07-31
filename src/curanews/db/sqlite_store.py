"""SQLite persistence for scraped news articles (Issue #5)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping


def canonical_url_hash(url: str) -> str:
    """Stable hash used for duplicate detection."""
    normalized = url.strip()
    return sha256(normalized.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class StoredArticle:
    article_id: str
    url: str
    url_hash: str
    title: str
    content: str
    published_date: str | None
    source: str
    category: str
    summary: str | None
    author: str | None
    scraped_at: str | None


class SqliteArticleStore:
    """Thin SQLite repository for pipeline persistence."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def close(self) -> None:
        self._conn.close()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                article_id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                url_hash TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                published_date TEXT,
                source TEXT NOT NULL,
                category TEXT NOT NULL,
                summary TEXT,
                author TEXT,
                scraped_at TEXT,
                metadata_json TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category)"
        )
        self._conn.commit()

    def exists_url_hash(self, url_hash: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM articles WHERE url_hash = ? LIMIT 1",
            (url_hash,),
        ).fetchone()
        return row is not None

    def insert_article(self, payload: Mapping[str, Any]) -> bool:
        """Insert article. Returns False if url_hash already exists."""
        url = str(payload["url"])
        url_hash = canonical_url_hash(url)
        if self.exists_url_hash(url_hash):
            return False

        metadata = payload.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {"value": metadata}

        self._conn.execute(
            """
            INSERT INTO articles (
                article_id, url, url_hash, title, content, published_date,
                source, category, summary, author, scraped_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(payload["article_id"]),
                url,
                url_hash,
                str(payload["title"]),
                str(payload["content"]),
                _as_text(payload.get("published_date")),
                str(payload["source"]),
                str(payload["category"]),
                _optional_text(payload.get("summary")),
                _optional_text(payload.get("author")),
                _as_text(payload.get("scraped_at")),
                json.dumps(metadata, ensure_ascii=False, default=str),
            ),
        )
        self._conn.commit()
        return True

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS c FROM articles").fetchone()
        return int(row["c"])

    def list_recent(self, limit: int = 10) -> list[StoredArticle]:
        rows = self._conn.execute(
            """
            SELECT article_id, url, url_hash, title, content, published_date,
                   source, category, summary, author, scraped_at
            FROM articles
            ORDER BY scraped_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            StoredArticle(
                article_id=row["article_id"],
                url=row["url"],
                url_hash=row["url_hash"],
                title=row["title"],
                content=row["content"],
                published_date=row["published_date"],
                source=row["source"],
                category=row["category"],
                summary=row["summary"],
                author=row["author"],
                scraped_at=row["scraped_at"],
            )
            for row in rows
        ]


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
