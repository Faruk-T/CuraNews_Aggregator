"""Database package — SQLite (Issue #5) + PostgreSQL ORM (Issue #11)."""

from curanews.db.base import Base
from curanews.db.models import Article, Entity, Source, User
from curanews.db.repository import ArticleRepository, SourceRepository
from curanews.db.session import get_engine, get_session_factory
from curanews.db.sqlite_store import SqliteArticleStore, canonical_url_hash

__all__ = [
    "Article",
    "ArticleRepository",
    "Base",
    "Entity",
    "Source",
    "SourceRepository",
    "SqliteArticleStore",
    "User",
    "canonical_url_hash",
    "get_engine",
    "get_session_factory",
]
