"""Extracted entity / topic span from NLP (Issue #14 / G14)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExtractedEntity:
    """Single NER or rule-based topic hit."""

    label: str
    ent_type: str
    normalized: str
    confidence: float | None = None
