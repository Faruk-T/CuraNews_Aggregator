"""Tag article text with spaCy + topics and persist links (G14)."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from curanews.db.entity_repository import EntityRepository
from curanews.db.models import Article
from curanews.nlp.spacy_pipe import SpacyPipe, get_spacy_pipe

logger = logging.getLogger(__name__)


def article_text_for_nlp(article: Article) -> str:
    parts = [article.title or ""]
    if article.summary:
        parts.append(article.summary)
    if article.body:
        parts.append(article.body)
    return "\n".join(p for p in parts if p.strip())


def tag_article(
    session: Session,
    article: Article,
    *,
    pipe: SpacyPipe | None = None,
) -> int:
    """Extract entities for one article and write ``article_entities`` links.

    Returns the number of **new** links created. Degrades when spaCy is down:
    rule-based TOPIC keywords still apply.
    """
    nlp = pipe or get_spacy_pipe()
    text = article_text_for_nlp(article)
    result = nlp.extract(text)
    repo = EntityRepository(session)
    created = repo.attach_extracted(article.id, result.entities)
    logger.info(
        "nlp tagged article_id=%s entities=%s new_links=%s degraded=%s",
        article.id,
        len(result.entities),
        created,
        result.degraded,
    )
    return created


def tag_article_id(
    session: Session,
    article_id: UUID,
    *,
    pipe: SpacyPipe | None = None,
) -> int:
    article = session.get(Article, article_id)
    if article is None:
        return 0
    return tag_article(session, article, pipe=pipe)
