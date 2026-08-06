"""Parse GNews-compatible JSON payloads (Issue #8)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from curanews.domain.models import RawArticleDraft
from curanews.scrapers.adapters._paths import fixture_path


def parse_gnews_payload(
    payload: dict[str, Any],
    *,
    source_id: str = "gnews_api",
    default_category: str = "general",
) -> list[RawArticleDraft]:
    """Map ``{ "articles": [...] }`` JSON to ``RawArticleDraft`` rows."""
    articles = payload.get("articles") or []
    drafts: list[RawArticleDraft] = []

    for row in articles:
        if not isinstance(row, dict):
            continue
        title = _text(row.get("title"))
        url = _text(row.get("url"))
        if not title or not url:
            continue
        description = _text(row.get("description"))
        content = _text(row.get("content")) or description or title
        published = _parse_datetime(row.get("publishedAt"))
        source_name = source_id
        nested = row.get("source")
        if isinstance(nested, dict) and nested.get("name"):
            source_name = f"{source_id}:{_text(nested.get('name'))}"

        drafts.append(
            RawArticleDraft(
                title=title,
                url=url,
                content=content,
                summary=description or content[:500],
                published_date=published,
                source=source_name,
                category=default_category,
                metadata={"provider": "gnews_compatible"},
            )
        )
    return drafts


def load_gnews_fixture(path: Path | None = None) -> list[RawArticleDraft]:
    fixture = path or fixture_path("tests", "fixtures", "gnews_sample.json")
    data = json.loads(fixture.read_text(encoding="utf-8"))
    return parse_gnews_payload(
        data,
        source_id="gnews_fixture",
        default_category="technology",
    )


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    cleaned = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
