"""Last RSS refresh result, kept in Redis with an in-process fallback."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from curanews.cache.redis_client import get_redis_client

STATUS_KEY = "rss_refresh:last"
STATUS_TTL_SECONDS = 7 * 24 * 3600
_memory: dict[str, Any] = {}


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def record_ingest_status(payload: dict[str, Any]) -> None:
    body = dict(payload)
    _memory.clear()
    _memory.update(body)
    raw = json.dumps(body, default=str)
    get_redis_client().setex(STATUS_KEY, STATUS_TTL_SECONDS, raw)


def read_ingest_status() -> dict[str, Any]:
    raw = get_redis_client().get(STATUS_KEY)
    if raw:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            return parsed
    return dict(_memory)
