"""Persist NLP entities and article links (Issue #14 / G14)."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from curanews.db.models import ArticleEntity, Entity


class ExtractedEntityLike(Protocol):
    label: str
    ent_type: str
    normalized: str
    confidence: float | None


class EntityRepository:
    """Ensure entity rows and link them to articles."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_type_and_normalized(self, ent_type: str, normalized: str) -> Entity | None:
        stmt = select(Entity).where(
            Entity.ent_type == ent_type,
            Entity.normalized == normalized,
        )
        return self._session.scalars(stmt).one_or_none()

    def ensure_entity(self, extracted: ExtractedEntityLike) -> Entity:
        existing = self.get_by_type_and_normalized(extracted.ent_type, extracted.normalized)
        if existing is not None:
            return existing
        row = Entity(
            label=extracted.label,
            ent_type=extracted.ent_type,
            normalized=extracted.normalized,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def link_article(
        self,
        article_id: UUID,
        entity_id: UUID,
        *,
        confidence: float | None = None,
    ) -> ArticleEntity | None:
        """Create article↔entity link; return None if already linked."""
        stmt = select(ArticleEntity).where(
            ArticleEntity.article_id == article_id,
            ArticleEntity.entity_id == entity_id,
        )
        existing = self._session.scalars(stmt).one_or_none()
        if existing is not None:
            return None
        link = ArticleEntity(
            article_id=article_id,
            entity_id=entity_id,
            confidence=confidence,
        )
        self._session.add(link)
        self._session.flush()
        return link

    def attach_extracted(
        self,
        article_id: UUID,
        extracted: list[ExtractedEntityLike],
    ) -> int:
        """Ensure entities and link them; return number of new links."""
        created = 0
        for item in extracted:
            entity = self.ensure_entity(item)
            link = self.link_article(article_id, entity.id, confidence=item.confidence)
            if link is not None:
                created += 1
        return created

    def list_for_article(self, article_id: UUID) -> list[Entity]:
        stmt = (
            select(Entity)
            .join(ArticleEntity, ArticleEntity.entity_id == Entity.id)
            .where(ArticleEntity.article_id == article_id)
        )
        return list(self._session.scalars(stmt).all())
