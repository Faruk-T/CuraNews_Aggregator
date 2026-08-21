"""Pydantic request/response models for the REST API (Issue #16 / G16)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"] = "ok"
    app: str
    version: str
    database: Literal["up", "down"] = "down"
    redis: Literal["up", "down"] = "down"


class ArticleItem(BaseModel):
    id: UUID
    title: str
    summary: str | None = None
    url: str
    source_name: str
    category: str | None = None
    published_at: datetime | None = None
    entities: list[str] = Field(default_factory=list)
    score: float | None = None
    read: bool = False
    read_at: datetime | None = None


class ArticleListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ArticleItem]


class FeedResponse(BaseModel):
    user_id: str
    generated_at: datetime
    cache: Literal["hit", "miss", "bypass"] = "miss"
    items: list[ArticleItem]
    read_items: list[ArticleItem] = Field(default_factory=list)
    inbox_grace_seconds: int = 1200


class ReadCreate(BaseModel):
    user_id: str = Field(min_length=1, description="external_key, e.g. demo-user-a")
    article_id: UUID
    dwell_ms: int | None = Field(default=None, ge=0)


class ReadResponse(BaseModel):
    user_id: str
    article_id: UUID
    read_at: datetime
    dwell_ms: int | None = None


class TopicItem(BaseModel):
    label: str
    ent_type: str
    normalized: str
    article_count: int


class TopicsResponse(BaseModel):
    items: list[TopicItem]
