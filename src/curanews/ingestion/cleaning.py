"""Text cleaning helpers for scraped news items (Issue #5, #10)."""

from __future__ import annotations

import re
from typing import Any, MutableMapping

from curanews.domain.models import RawArticleDraft

_WHITESPACE_RE = re.compile(r"\s+")
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def collapse_whitespace(value: str) -> str:
    return _WHITESPACE_RE.sub(" ", value).strip()


def strip_html_tags(value: str) -> str:
    """Remove HTML markup and collapse whitespace (Issue #10)."""
    without_tags = _HTML_TAG_RE.sub(" ", value)
    return collapse_whitespace(without_tags)


def clean_news_payload(payload: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Normalize string fields in-place and return the payload."""
    for key in ("title", "source", "author"):
        value = payload.get(key)
        if isinstance(value, str):
            payload[key] = collapse_whitespace(value)

    for key in ("content", "summary"):
        value = payload.get(key)
        if isinstance(value, str):
            payload[key] = strip_html_tags(value)

    category = payload.get("category")
    if isinstance(category, str):
        payload["category"] = collapse_whitespace(category).lower().replace(" ", "-")

    url = payload.get("url")
    if isinstance(url, str):
        payload["url"] = url.strip()

    return payload


def clean_raw_draft(draft: RawArticleDraft) -> RawArticleDraft:
    """Apply the same cleaning rules to adapter drafts before promotion."""
    data = draft.model_dump()
    cleaned = clean_news_payload(data)
    return RawArticleDraft.model_validate(cleaned)
