"""Verify spaCy / topic NLP and entity persistence (Issue #14 / G14).

Usage::

    poetry run python -m spacy download en_core_web_sm
    poetry run python scripts/verify_spacy_nlp.py
    poetry run python scripts/verify_spacy_nlp.py --require-model
    poetry run python scripts/verify_spacy_nlp.py --persist
"""

from __future__ import annotations

import argparse
import json
import sys

from sqlalchemy import select

from curanews.config import get_settings
from curanews.db.entity_repository import EntityRepository
from curanews.db.models import Article, Source
from curanews.db.repository import content_hash
from curanews.db.session import get_session_factory
from curanews.db.sqlite_store import canonical_url_hash
from curanews.logging_setup import setup_logging
from curanews.nlp.spacy_pipe import SpacyModelUnavailableError, SpacyPipe
from curanews.nlp.tagging import tag_article

SAMPLE_TEXT = (
    "OpenAI announced new models in London as artificial intelligence and "
    "technology markets rally on rate-cut hopes."
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Demonstrate spaCy NER + topic tagging.")
    parser.add_argument(
        "--require-model",
        action="store_true",
        help="Exit non-zero if spaCy model cannot be loaded",
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Also write a demo article + entities to PostgreSQL",
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    setup_logging(settings.log_level, app_name="curanews")
    pipe = SpacyPipe(settings.spacy_model)

    if args.require_model:
        try:
            pipe.require_model()
        except SpacyModelUnavailableError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    result = pipe.extract(SAMPLE_TEXT)
    payload: dict = {
        "model_name": result.model_name or settings.spacy_model,
        "model_available": pipe.available,
        "degraded": result.degraded,
        "reason": result.reason,
        "sample": SAMPLE_TEXT,
        "entities": [
            {
                "label": e.label,
                "ent_type": e.ent_type,
                "normalized": e.normalized,
                "confidence": e.confidence,
            }
            for e in result.entities
        ],
    }

    has_expected = any(e.ent_type in {"ORG", "GPE", "TOPIC"} for e in result.entities)
    if not has_expected:
        print(json.dumps(payload, indent=2))
        print("expected at least one ORG/GPE/TOPIC entity", file=sys.stderr)
        return 1

    if args.persist:
        factory = get_session_factory()
        session = factory()
        try:
            source = session.scalars(select(Source).where(Source.name == "example_news")).one_or_none()
            if source is None:
                source = Source(
                    name="example_news",
                    base_url="https://example.com/",
                    kind="static",
                )
                session.add(source)
                session.flush()

            url = "https://example.com/news/spacy-nlp-demo-2026"
            url_hash = canonical_url_hash(url)
            article = session.scalars(select(Article).where(Article.url_hash == url_hash)).one_or_none()
            if article is None:
                article = Article(
                    source_id=source.id,
                    url=url,
                    url_hash=url_hash,
                    title="OpenAI expands in London",
                    body=SAMPLE_TEXT,
                    content_hash=content_hash(SAMPLE_TEXT),
                    category="tech",
                    language="en",
                )
                session.add(article)
                session.flush()

            new_links = tag_article(session, article, pipe=pipe)
            session.commit()
            linked = EntityRepository(session).list_for_article(article.id)
            payload["persist"] = {
                "article_id": str(article.id),
                "new_links": new_links,
                "entity_count": len(linked),
                "entities": [e.label for e in linked],
            }
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            print(f"persist failed: {exc}", file=sys.stderr)
            return 1
        finally:
            session.close()

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
