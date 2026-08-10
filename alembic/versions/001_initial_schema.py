"""Initial PostgreSQL schema — IMPLEMENTATION_PLAN §7.2.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-08-07

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_key", sa.String(length=120), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("robots_respected", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sources_name", "sources", ["name"], unique=True)
    op.create_table(
        "articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("url_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("author_display", sa.String(length=200), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("raw_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_articles_source_id", "articles", ["source_id"])
    op.create_table(
        "entities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("label", sa.String(length=300), nullable=False),
        sa.Column("ent_type", sa.String(length=64), nullable=False),
        sa.Column("normalized", sa.String(length=300), nullable=False),
    )
    op.create_table(
        "article_entities",
        sa.Column("article_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("articles.id"), primary_key=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("entities.id"), primary_key=True),
        sa.Column("confidence", sa.Float(), nullable=True),
    )
    op.create_table(
        "user_reads",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("article_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("articles.id"), primary_key=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dwell_ms", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("user_reads")
    op.drop_table("article_entities")
    op.drop_table("entities")
    op.drop_index("ix_articles_source_id", table_name="articles")
    op.drop_table("articles")
    op.drop_index("ix_sources_name", table_name="sources")
    op.drop_table("sources")
    op.drop_table("users")
