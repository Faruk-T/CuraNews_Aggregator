"""Smoke-check docker compose stack: /health then /feed (Issue #20 / G20).

Usage::

    docker compose up -d --build
    poetry run python scripts/compose_smoke.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("CURANEWS_API_BASE", "http://127.0.0.1:8001").rstrip("/")


def _get(path: str) -> tuple[int, dict | list | str]:
    req = urllib.request.Request(f"{BASE}{path}", method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode("utf-8")
        try:
            return resp.status, json.loads(body)
        except json.JSONDecodeError:
            return resp.status, body


def main() -> int:
    deadline = time.time() + 120
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            status, payload = _get("/health")
            if status == 200 and isinstance(payload, dict) and payload.get("database") == "up":
                print(json.dumps({"health": payload}, indent=2))
                break
            last_err = RuntimeError(f"health not ready: {payload}")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = exc
        time.sleep(2)
    else:
        print(f"compose smoke failed waiting for /health: {last_err}", file=sys.stderr)
        return 1

    try:
        status, feed = _get("/feed?user_id=demo-user-a&limit=5")
    except urllib.error.HTTPError as exc:
        print(f"/feed HTTP {exc.code}: {exc.read().decode()}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"/feed failed: {exc}", file=sys.stderr)
        return 1

    if status != 200 or not isinstance(feed, dict):
        print(f"unexpected feed response: {status} {feed}", file=sys.stderr)
        return 1

    items = feed.get("items") or []
    summary = {
        "user_id": feed.get("user_id"),
        "cache": feed.get("cache"),
        "item_count": len(items),
        "titles": [i.get("title") for i in items[:3]],
    }
    print(json.dumps({"feed": summary}, indent=2))
    if not items:
        print("warning: feed empty — bootstrap RSS may still be running", file=sys.stderr)
        return 2
    print("compose smoke OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
