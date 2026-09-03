"""Intelligent category classification and breaking news detection (Day 21).

Provides multi-class classification for Turkish news:
- Gündem (agenda/current events)
- Ekonomi (finance/markets)
- Teknoloji (tech/AI/software)
- Spor (football/basketball/athletics)
- Sağlık (health/medicine)
- Dünya (international/world)
- Politika (politics/governance)

Also detects breaking news ("Son Dakika") and estimates read time.
"""

from __future__ import annotations

import math
import re
from typing import Final

CANONICAL_CATEGORIES: Final[dict[str, str]] = {
    "gundem": "Gündem",
    "ekonomi": "Ekonomi",
    "teknoloji": "Teknoloji",
    "spor": "Spor",
    "saglik": "Sağlık",
    "dunya": "Dünya",
    "politika": "Politika",
}

# Category keyword dictionaries with weights
CATEGORY_WEIGHTS: Final[dict[str, dict[str, float]]] = {
    "ekonomi": {
        "faiz": 2.5,
        "enflasyon": 3.0,
        "dolar": 2.2,
        "euro": 2.0,
        "borsa": 2.5,
        "bist": 3.0,
        "merkez bankası": 3.0,
        "tcmb": 3.0,
        "fed": 2.0,
        "altın": 2.0,
        "kripto": 2.5,
        "bitcoin": 2.5,
        "piyasa": 1.8,
        "şirket": 1.2,
        "gelir": 1.5,
        "vergi": 2.0,
        "ihracat": 2.2,
        "ithalat": 2.2,
        "maaş": 2.0,
        "zam": 2.0,
        "asgari ücret": 3.0,
        "hisse": 2.0,
        "fon": 1.8,
        "finans": 2.2,
        "economy": 2.5,
        "markets": 2.0,
        "inflation": 2.5,
        "interest rate": 2.5,
    },
    "teknoloji": {
        "yapay zeka": 3.5,
        "ai": 2.5,
        "yazılım": 2.5,
        "donanım": 2.0,
        "siber": 2.5,
        "robot": 2.0,
        "apple": 2.0,
        "google": 2.0,
        "microsoft": 2.0,
        "chatgpt": 3.0,
        "openai": 3.0,
        "akıllı telefon": 2.5,
        "uygulama": 1.8,
        "çip": 2.5,
        "semiconductor": 2.5,
        "uzay": 2.0,
        "nasa": 2.5,
        "spacex": 2.5,
        "teknoloji": 2.5,
        "tech": 2.5,
        "software": 2.0,
        "hardware": 2.0,
        "siber güvenlik": 3.0,
        "metaverse": 2.0,
        "kuantum": 2.5,
    },
    "spor": {
        "futbol": 3.0,
        "basketbol": 3.0,
        "voleybol": 3.0,
        "süper lig": 3.5,
        "şampiyonlar ligi": 3.5,
        "galatasaray": 2.8,
        "fenerbahçe": 2.8,
        "beşiktaş": 2.8,
        "trabzonspor": 2.8,
        "milli takım": 2.5,
        "gol": 2.5,
        "maç": 2.0,
        "derbi": 3.0,
        "transfer": 2.2,
        "teknik direktör": 2.0,
        "olimpiyat": 3.0,
        "madalya": 2.5,
        "championship": 2.5,
        "league": 2.0,
        "sports": 2.5,
        "spor": 2.5,
    },
    "saglik": {
        "sağlık": 2.5,
        "hastane": 2.5,
        "doktor": 2.0,
        "ilaç": 2.5,
        "tedavi": 2.5,
        "hastalık": 2.2,
        "virüs": 2.5,
        "aşı": 2.8,
        "kanser": 2.5,
        "beslenme": 2.0,
        "diyabet": 2.5,
        "kalp": 2.0,
        "ameliyat": 2.2,
        "tıp": 2.5,
        "sağlık bakanlığı": 3.0,
        "health": 2.5,
        "medical": 2.5,
    },
    "politika": {
        "seçim": 2.5,
        "tbmm": 3.0,
        "meclis": 2.5,
        "cumhurbaşkanı": 2.5,
        "bakan": 2.0,
        "parti": 2.0,
        "chp": 2.2,
        "ak parti": 2.2,
        "mhp": 2.2,
        "hükümet": 2.2,
        "anayasa": 2.5,
        "yasa": 2.0,
        "milletvekili": 2.5,
        "politika": 2.5,
        "politics": 2.5,
        "diplomasi": 2.2,
    },
    "dunya": {
        "abd": 2.0,
        "rusya": 2.0,
        "ukrayna": 2.2,
        "israil": 2.2,
        "gazze": 2.5,
        "filistin": 2.5,
        "avrupa birliği": 2.5,
        "nato": 2.5,
        "birleşmiş milletler": 2.5,
        "beyaz saray": 2.2,
        "kremlin": 2.2,
        "çine": 1.5,
        "iran": 2.0,
        "dünya": 2.0,
        "world": 2.0,
        "uluslararası": 2.0,
        "savaş": 2.0,
        "ateşkes": 2.5,
    },
    "gundem": {
        "asayiş": 2.5,
        "kaza": 2.0,
        "yangın": 2.2,
        "deprem": 3.0,
        "afad": 3.0,
        "meteoroloji": 2.5,
        "hava durumu": 2.5,
        "trafik": 2.0,
        "valilik": 2.0,
        "belediye": 1.8,
        "polis": 2.0,
        "jandarma": 2.0,
        "operasyon": 2.0,
        "gündem": 2.0,
    },
}

BREAKING_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"\bson\s*dakika\b", re.IGNORECASE),
    re.compile(r"\bflaş\s*(haber)?\b", re.IGNORECASE),
    re.compile(r"\bacil\s*gelişme\b", re.IGNORECASE),
    re.compile(r"\bsıcak\s*gelişme\b", re.IGNORECASE),
    re.compile(r"\bbreaking\s*(news)?\b", re.IGNORECASE),
    re.compile(r"^\s*\[?(son dakika|flaş)\]?", re.IGNORECASE),
]


def detect_breaking_news(title: str, summary: str = "") -> bool:
    """Check if the title or summary contains breaking news indicators."""
    text = f"{title} {summary}"
    return any(pat.search(text) for pat in BREAKING_PATTERNS)


def calculate_read_time(text: str, summary: str = "") -> int:
    """Calculate read time in minutes, minimum 1 minute."""
    full = f"{text} {summary}".strip()
    if not full:
        return 1
    words = len(re.findall(r"\w+", full))
    return max(1, math.ceil(words / 180))


def normalize_category_name(raw: str | None) -> str | None:
    """Normalize raw category names from RSS or legacy tags."""
    if not raw:
        return None
    key = raw.strip().lower()
    mapping = {
        "gundem": "gundem",
        "gündem": "gundem",
        "turkey": "gundem",
        "türkiye": "gundem",
        "güncel": "gundem",
        "general": "gundem",
        "ekonomi": "ekonomi",
        "economy": "ekonomi",
        "finans": "ekonomi",
        "markets": "ekonomi",
        "teknoloji": "teknoloji",
        "tech": "teknoloji",
        "technology": "teknoloji",
        "bilim": "teknoloji",
        "science": "teknoloji",
        "spor": "spor",
        "sports": "spor",
        "sport": "spor",
        "futbol": "spor",
        "saglik": "saglik",
        "sağlık": "saglik",
        "health": "saglik",
        "dunya": "dunya",
        "dünya": "dunya",
        "world": "dunya",
        "dış haberler": "dunya",
        "politika": "politika",
        "siyaset": "politika",
        "politics": "politika",
    }
    return mapping.get(key)


def categorize_text(
    title: str,
    summary: str = "",
    body: str = "",
    default_category: str | None = None,
) -> tuple[str, float]:
    """Score text against canonical categories using weighted keyword heuristics.

    Returns:
        (category_slug, confidence_score)
    """
    normalized_default = normalize_category_name(default_category)

    # If already a specific mapped category, add initial prior weight
    scores: dict[str, float] = {k: 0.0 for k in CANONICAL_CATEGORIES}
    if normalized_default and normalized_default in scores:
        scores[normalized_default] += 1.5

    # Title has 3x weight, summary 1.5x, body 1x
    title_lower = title.lower()
    summary_lower = summary.lower()
    body_lower = body.lower()

    for cat, kw_dict in CATEGORY_WEIGHTS.items():
        cat_score = 0.0
        for kw, weight in kw_dict.items():
            pattern = r"(?<!\w)" + re.escape(kw) + r"(?!\w)"
            if re.search(pattern, title_lower):
                cat_score += weight * 3.0
            if re.search(pattern, summary_lower):
                cat_score += weight * 1.5
            if body_lower and re.search(pattern, body_lower):
                cat_score += weight * 1.0
        scores[cat] += cat_score

    best_cat, best_score = max(scores.items(), key=lambda kv: kv[1])
    if best_score <= 0.0:
        return normalized_default or "gundem", 0.3

    confidence = min(1.0, round(best_score / (best_score + 3.0), 2))
    return best_cat, confidence


def get_category_display_name(slug: str | None) -> str:
    """Return human readable category name."""
    if not slug:
        return "Gündem"
    canonical = normalize_category_name(slug)
    return CANONICAL_CATEGORIES.get(canonical or slug, slug.capitalize())
