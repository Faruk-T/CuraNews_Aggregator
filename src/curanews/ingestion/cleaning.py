"""Text cleaning helpers for scraped news items."""

from __future__ import annotations

import re
from typing import Any, MutableMapping

_WHITESPACE_RE = re.compile(r"\s+")


def collapse_whitespace(value: str) -> str:
    return _WHITESPACE_RE.sub(" ", value).strip()


def clean_news_payload(payload: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Normalize string fields in-place and return the payload."""
    for key in ("title", "content", "summary", "source", "author"):
        value = payload.get(key)
        if isinstance(value, str):
            payload[key] = collapse_whitespace(value)

    category = payload.get("category")
    if isinstance(category, str):
        payload["category"] = collapse_whitespace(category).lower().replace(" ", "-")

    url = payload.get("url")
    if isinstance(url, str):
        payload["url"] = url.strip()

    return payload
