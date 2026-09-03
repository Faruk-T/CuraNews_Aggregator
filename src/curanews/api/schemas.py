"""Pydantic request/response models for the REST API (Issue #16 / G16)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
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
    body: str | None = None
    url: str
    source_name: str
    source_logo: str | None = None
    image_url: str | None = None
    video_url: str | None = None
    category: str | None = None
    category_name: str | None = None
    is_breaking: bool = False
    is_editorial: bool = False
    is_bookmarked: bool = False
    comments_count: int = 0
    author_display: str | None = None
    author_title: str | None = None
    author_avatar: str | None = None
    read_time_minutes: int = 1
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


# ========================================================
# AUTH & PROFILE SCHEMAS (DAY 22)
# ========================================================
class UserRegister(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: str
    avatar_url: str | None = None
    role: str = "reader"
    preferences: dict[str, Any] = Field(default_factory=dict)


class UserLogin(BaseModel):
    email: str
    password: str


class UserProfile(BaseModel):
    id: UUID
    external_key: str
    email: str | None = None
    full_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    role: str = "reader"
    preferences: dict[str, Any] = Field(default_factory=dict)
    read_count: int = 0
    bookmarks_count: int = 0


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


# ========================================================
# BOOKMARK SCHEMAS (DAY 22)
# ========================================================
class BookmarkToggleRequest(BaseModel):
    article_id: UUID
    user_id: str | None = None


class BookmarkToggleResponse(BaseModel):
    article_id: UUID
    is_bookmarked: bool
    total_bookmarks: int


class BookmarkListResponse(BaseModel):
    total: int
    items: list[ArticleItem]


# ========================================================
# COMMENT SCHEMAS (DAY 22)
# ========================================================
class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    author_name: str | None = None
    author_avatar: str | None = None


class CommentItem(BaseModel):
    id: UUID
    article_id: UUID
    author_name: str
    author_avatar: str | None = None
    content: str
    likes: int = 0
    created_at: datetime


class CommentListResponse(BaseModel):
    article_id: UUID
    total: int
    items: list[CommentItem]


class CommentLikeResponse(BaseModel):
    comment_id: UUID
    likes: int


# ========================================================
# ONEDIO STYLE EDITOR CMS SCHEMAS (DAY 22)
# ========================================================
class EditorArticleCreate(BaseModel):
    title: str = Field(min_length=5, max_length=300)
    category: str = "gundem"
    summary: str = Field(min_length=10, max_length=600)
    body: str = Field(min_length=20)
    image_url: str | None = None
    video_url: str | None = None
    author_name: str = "CuraNews Editörü"
    author_title: str = "Kıdemli Editör"
    author_avatar: str | None = None

