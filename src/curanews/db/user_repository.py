"""User and read-history helpers (Issue #15 / G15)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from curanews.db.models import ArticleEntity, Entity, User, UserRead


class UserRepository:
    """Lookup / seed users and record read events."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_external_key(self, external_key: str) -> User | None:
        stmt = select(User).where(User.external_key == external_key)
        return self._session.scalars(stmt).one_or_none()

    def ensure_user(self, external_key: str) -> User:
        existing = self.get_by_external_key(external_key)
        if existing is not None:
            return existing
        row = User(external_key=external_key)
        self._session.add(row)
        self._session.flush()
        return row

    def record_read(
        self,
        user_id: UUID,
        article_id: UUID,
        *,
        dwell_ms: int | None = None,
        read_at: datetime | None = None,
    ) -> UserRead:
        stmt = select(UserRead).where(
            UserRead.user_id == user_id,
            UserRead.article_id == article_id,
        )
        existing = self._session.scalars(stmt).one_or_none()
        if existing is not None:
            if dwell_ms is not None:
                existing.dwell_ms = dwell_ms
            return existing
        row = UserRead(
            user_id=user_id,
            article_id=article_id,
            read_at=read_at or datetime.now(timezone.utc),
            dwell_ms=dwell_ms,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def entity_profile(self, user_id: UUID) -> set[str]:
        """Return normalized entity labels from articles the user has read."""
        stmt = (
            select(Entity.normalized)
            .join(ArticleEntity, ArticleEntity.entity_id == Entity.id)
            .join(UserRead, UserRead.article_id == ArticleEntity.article_id)
            .where(UserRead.user_id == user_id)
        )
        return {row for row in self._session.scalars(stmt).all()}

    def article_entity_set(self, article_id: UUID) -> set[str]:
        stmt = (
            select(Entity.normalized)
            .join(ArticleEntity, ArticleEntity.entity_id == Entity.id)
            .where(ArticleEntity.article_id == article_id)
        )
        return {row for row in self._session.scalars(stmt).all()}
