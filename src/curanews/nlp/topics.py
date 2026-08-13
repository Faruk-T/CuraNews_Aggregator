"""Rule-based topic keywords for TR/EN when spaCy topics are thin (G14)."""

from __future__ import annotations

import re

from curanews.nlp.entities import ExtractedEntity

# Keyword → topic slug (lowercase match on whole words / phrases)
TOPIC_KEYWORDS: dict[str, str] = {
    "yapay zeka": "ai",
    "artificial intelligence": "ai",
    "machine learning": "ai",
    "makine öğrenmesi": "ai",
    "openai": "ai",
    "chatgpt": "ai",
    "ekonomi": "economy",
    "economy": "economy",
    "markets": "economy",
    "interest rate": "economy",
    "faiz": "economy",
    "spor": "sports",
    "sports": "sports",
    "championship": "sports",
    "iklim": "climate",
    "climate": "climate",
    "warming": "climate",
    "teknoloji": "technology",
    "technology": "technology",
    "open source": "technology",
}


def match_topic_keywords(text: str) -> list[ExtractedEntity]:
    """Return TOPIC entities from a fixed keyword list (TR + EN)."""
    lowered = text.lower()
    found: list[ExtractedEntity] = []
    seen: set[str] = set()
    # Longer phrases first to prefer multi-word matches
    for phrase, slug in sorted(TOPIC_KEYWORDS.items(), key=lambda kv: -len(kv[0])):
        if slug in seen:
            continue
        pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            seen.add(slug)
            found.append(
                ExtractedEntity(
                    label=f"TOPIC:{slug}",
                    ent_type="TOPIC",
                    normalized=slug,
                    confidence=0.7,
                )
            )
    return found
