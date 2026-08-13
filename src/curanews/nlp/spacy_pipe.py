"""spaCy NER pipeline with graceful degrade (Issue #14 / G14)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from curanews.config import get_settings
from curanews.nlp.entities import ExtractedEntity
from curanews.nlp.topics import match_topic_keywords

logger = logging.getLogger(__name__)

# spaCy entity labels we keep for news tagging
_KEEP_LABELS = frozenset({"PERSON", "ORG", "GPE", "LOC", "PRODUCT", "EVENT", "NORP"})


class SpacyModelUnavailableError(RuntimeError):
    """Raised when the configured spaCy model cannot be loaded."""


@dataclass(slots=True)
class SpacyPipeResult:
    """Outcome of running NLP on a text blob."""

    entities: list[ExtractedEntity]
    model_name: str | None
    degraded: bool
    reason: str | None = None


def normalize_label(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _entity_from_span(label: str, ent_type: str, confidence: float | None = None) -> ExtractedEntity:
    normalized = normalize_label(label)
    return ExtractedEntity(
        label=f"{ent_type}:{label.strip()}",
        ent_type=ent_type,
        normalized=normalized,
        confidence=confidence,
    )


def _dedupe(entities: list[ExtractedEntity]) -> list[ExtractedEntity]:
    seen: set[tuple[str, str]] = set()
    out: list[ExtractedEntity] = []
    for ent in entities:
        key = (ent.ent_type, ent.normalized)
        if key in seen:
            continue
        seen.add(key)
        out.append(ent)
    return out


class SpacyPipe:
    """Load spaCy once and extract entities + rule-based topics."""

    def __init__(self, model_name: str | None = None, *, nlp: Any | None = None) -> None:
        self.model_name = model_name or get_settings().spacy_model
        self._nlp = nlp
        self._load_error: str | None = None
        if self._nlp is None:
            self._try_load()

    def _try_load(self) -> None:
        try:
            import spacy

            self._nlp = spacy.load(self.model_name)
            logger.info("spacy model loaded name=%s", self.model_name)
        except Exception as exc:  # noqa: BLE001 — degrade on any load failure
            self._nlp = None
            self._load_error = str(exc)
            logger.warning(
                "spacy unavailable degrade=true model=%s error=%s",
                self.model_name,
                exc,
            )

    @property
    def available(self) -> bool:
        return self._nlp is not None

    def extract(self, text: str) -> SpacyPipeResult:
        """Extract NER entities (if model up) plus keyword topics always."""
        blob = (text or "").strip()
        entities: list[ExtractedEntity] = []
        degraded = False
        reason: str | None = None

        if not blob:
            return SpacyPipeResult(
                entities=[],
                model_name=self.model_name if self.available else None,
                degraded=not self.available,
                reason=self._load_error or "empty_text",
            )

        if self.available:
            doc = self._nlp(blob)
            for ent in doc.ents:
                if ent.label_ not in _KEEP_LABELS:
                    continue
                entities.append(_entity_from_span(ent.text, ent.label_, confidence=0.9))
        else:
            degraded = True
            reason = self._load_error or "model_not_loaded"
            logger.info("spacy extract degraded reason=%s", reason)

        entities.extend(match_topic_keywords(blob))
        return SpacyPipeResult(
            entities=_dedupe(entities),
            model_name=self.model_name if self.available else None,
            degraded=degraded,
            reason=reason,
        )

    def require_model(self) -> None:
        """Fail fast when a live model is mandatory (CLI verify)."""
        if not self.available:
            raise SpacyModelUnavailableError(
                f"spaCy model {self.model_name!r} is not available: {self._load_error}. "
                f"Install with: poetry run python -m spacy download {self.model_name}"
            )


@lru_cache(maxsize=1)
def get_spacy_pipe() -> SpacyPipe:
    return SpacyPipe()
