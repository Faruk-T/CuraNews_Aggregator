"""Demonstrate feed cache HIT/MISS and read-driven re-rank (Issue #17 / G17).

Usage::

    docker compose up -d postgres redis
    poetry run python scripts/seed_demo_users.py
    poetry run python scripts/run_api.py
    # other terminal:
    poetry run python scripts/verify_api_feed_cache.py
"""

from __future__ import annotations

import json
import sys

import httpx

from curanews.config import get_settings


def main() -> int:
    settings = get_settings()
    base = f"http://127.0.0.1:{settings.api_port}"
    user = "demo-user-a"

    with httpx.Client(base_url=base, timeout=10.0) as client:
        health = client.get("/health")
        if health.status_code != 200:
            print("API not reachable — start with: poetry run python scripts/run_api.py", file=sys.stderr)
            return 1

        first = client.get("/feed", params={"user_id": user, "limit": 5})
        second = client.get("/feed", params={"user_id": user, "limit": 5})
        if first.status_code != 200 or second.status_code != 200:
            print(first.text, second.text, file=sys.stderr)
            return 1

        items = first.json().get("items") or []
        if not items:
            print("empty feed — run seed_demo_users.py", file=sys.stderr)
            return 1

        # Prefer an article that is not currently rank #1 to force a visible shift
        target = items[-1] if len(items) > 1 else items[0]
        read = client.post(
            "/reads",
            json={"user_id": user, "article_id": target["id"], "dwell_ms": 8000},
        )
        third = client.get("/feed", params={"user_id": user, "limit": 5})

        payload = {
            "health": health.json(),
            "first": {
                "cache": first.json()["cache"],
                "x_cache": first.headers.get("X-Cache"),
                "top": [i["title"] for i in first.json()["items"][:3]],
            },
            "second": {
                "cache": second.json()["cache"],
                "x_cache": second.headers.get("X-Cache"),
            },
            "read_article": target["title"],
            "read_status": read.status_code,
            "third_after_read": {
                "cache": third.json()["cache"],
                "x_cache": third.headers.get("X-Cache"),
                "top": [i["title"] for i in third.json()["items"][:3]],
            },
            "miss_then_hit": first.json()["cache"] == "miss" and second.json()["cache"] == "hit",
            "recomputed_after_read": third.json()["cache"] == "miss",
        }
        print(json.dumps(payload, indent=2))
        ok = payload["miss_then_hit"] and payload["recomputed_after_read"] and read.status_code == 201
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
