"""Community, auth, bookmarks, comments and editor features — Day 22 / Day 23.

Revision ID: 002_community_and_editor_features
Revises: 001_initial_schema
Create Date: 2026-09-03

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_community_and_editor_features"
down_revision: str | None = "001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Extend users table
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column("hashed_password", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("full_name", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("avatar_url", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("bio", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("role", sa.String(length=32), nullable=False, server_default="reader")
        )
        batch_op.add_column(
            sa.Column("preferences", sa.JSON(), nullable=False, server_default="{}")
        )

    # 2. Create user_bookmarks table
    op.create_table(
        "user_bookmarks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "article_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("articles.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "article_id", name="uq_user_bookmark"),
    )

    # 3. Create comments table
    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "article_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("articles.id"),
            nullable=False,
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True
        ),
        sa.Column("author_name", sa.String(length=120), nullable=False),
        sa.Column("author_avatar", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("likes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_comments_article_id", "comments", ["article_id"])


def downgrade() -> None:
    op.drop_index("ix_comments_article_id", table_name="comments")
    op.drop_table("comments")
    op.drop_table("user_bookmarks")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("preferences")
        batch_op.drop_column("role")
        batch_op.drop_column("bio")
        batch_op.drop_column("avatar_url")
        batch_op.drop_column("full_name")
        batch_op.drop_column("hashed_password")
        batch_op.drop_column("email")
