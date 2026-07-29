"""Domain models for normalized news articles (Issue #3)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator


REQUIRED_NEWS_FIELDS: tuple[str, ...] = (
    "article_id",
    "title",
    "url",
    "content",
    "published_date",
    "source",
    "category",
)


class NewsArticle(BaseModel):
    """Canonical news article schema used across scrapers, DB, and API.

    Required fields follow GitHub Issue #3 to prevent silent data corruption
    when incomplete scrape payloads slip through pipelines.
    """

    article_id: UUID = Field(default_factory=uuid4, description="Unique article identifier")
    title: str = Field(min_length=1, max_length=500)
    url: HttpUrl
    content: str = Field(min_length=1, description="Main article body / text")
    published_date: datetime
    source: str = Field(min_length=1, max_length=200, description="Publisher / site key")
    category: str = Field(min_length=1, max_length=120)

    summary: str | None = Field(default=None, max_length=2000)
    author: str | None = Field(default=None, max_length=200)
    language: str | None = Field(default=None, max_length=16)
    scraped_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("title", "content", "source", "category")
    @classmethod
    def strip_nonempty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field must not be blank or whitespace-only")
        return cleaned

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        return value.strip().lower().replace(" ", "-")


class RawArticleDraft(BaseModel):
    """Loose scrape draft before strict ``NewsArticle`` validation.

    Spiders may emit partial drafts; ingestion must promote them to
    ``NewsArticle`` (all required fields present) before persistence.
    """

    title: str | None = None
    url: str | None = None
    content: str | None = None
    published_date: datetime | None = None
    source: str | None = None
    category: str | None = None
    summary: str | None = None
    author: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
