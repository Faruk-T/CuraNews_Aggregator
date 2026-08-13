"""spaCy NLP and entity persistence tests (Issue #14 / G14)."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from curanews.db.base import Base
from curanews.db.entity_repository import EntityRepository
from curanews.db.models import Article, Source
from curanews.nlp.entities import ExtractedEntity
from curanews.nlp.spacy_pipe import SpacyPipe
from curanews.nlp.tagging import tag_article
from curanews.nlp.topics import match_topic_keywords


class _FakeSpan:
    def __init__(self, text: str, label: str) -> None:
        self.text = text
        self.label_ = label


class _FakeDoc:
    def __init__(self, ents: list[_FakeSpan]) -> None:
        self.ents = ents


class _FakeNlp:
    def __call__(self, text: str) -> _FakeDoc:
        return _FakeDoc(
            [
                _FakeSpan("OpenAI", "ORG"),
                _FakeSpan("London", "GPE"),
            ]
        )


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()


def test_topic_keywords_detect_ai_and_economy() -> None:
    hits = match_topic_keywords(
        "Open-source models and artificial intelligence reshape markets and the economy."
    )
    types = {h.ent_type for h in hits}
    slugs = {h.normalized for h in hits}
    assert "TOPIC" in types
    assert "ai" in slugs
    assert "economy" in slugs or "technology" in slugs


def test_spacy_pipe_extracts_org_with_fake_model() -> None:
    pipe = SpacyPipe(model_name="fake", nlp=_FakeNlp())
    result = pipe.extract("OpenAI opens an office in London amid technology shifts.")
    assert result.degraded is False
    assert any(e.ent_type == "ORG" and e.normalized == "openai" for e in result.entities)
    assert any(e.ent_type == "GPE" for e in result.entities)
    assert any(e.ent_type == "TOPIC" for e in result.entities)


def test_spacy_pipe_degrades_without_model() -> None:
    pipe = SpacyPipe(model_name="missing_model_xyz_not_installed")
    # Force unavailable without waiting on a real load if already loaded somehow
    pipe._nlp = None
    pipe._load_error = "model missing"
    result = pipe.extract("Yapay zeka ve ekonomi haberleri bugün öne çıktı.")
    assert result.degraded is True
    assert result.model_name is None
    assert any(e.ent_type == "TOPIC" and e.normalized == "ai" for e in result.entities)


def test_entity_repository_links_article(session: Session) -> None:
    source = Source(name="demo", base_url="https://example.com/", kind="static")
    session.add(source)
    session.flush()
    article = Article(
        source_id=source.id,
        url="https://example.com/news/nlp",
        url_hash="a" * 64,
        title="OpenAI in London",
        body="Artificial intelligence news.",
        content_hash="b" * 64,
        published_at=datetime(2026, 8, 13, tzinfo=timezone.utc),
        category="tech",
    )
    session.add(article)
    session.flush()

    repo = EntityRepository(session)
    created = repo.attach_extracted(
        article.id,
        [
            ExtractedEntity(label="ORG:OpenAI", ent_type="ORG", normalized="openai", confidence=0.9),
            ExtractedEntity(label="TOPIC:ai", ent_type="TOPIC", normalized="ai", confidence=0.7),
        ],
    )
    assert created == 2
    # Idempotent second attach
    assert repo.attach_extracted(
        article.id,
        [ExtractedEntity(label="ORG:OpenAI", ent_type="ORG", normalized="openai")],
    ) == 0
    linked = repo.list_for_article(article.id)
    assert {e.normalized for e in linked} == {"openai", "ai"}


def test_tag_article_persists_entities(session: Session) -> None:
    source = Source(name="demo2", base_url="https://example.com/", kind="static")
    session.add(source)
    session.flush()
    article = Article(
        source_id=source.id,
        url="https://example.com/news/tag",
        url_hash="c" * 64,
        title="OpenAI expands",
        body="Artificial intelligence and technology markets rally.",
        content_hash="d" * 64,
        category="tech",
    )
    session.add(article)
    session.flush()

    pipe = SpacyPipe(model_name="fake", nlp=_FakeNlp())
    created = tag_article(session, article, pipe=pipe)
    assert created >= 1
    session.commit()
    entities = EntityRepository(session).list_for_article(article.id)
    assert any(e.ent_type == "ORG" for e in entities)
