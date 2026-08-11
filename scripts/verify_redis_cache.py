"""Verify Redis feed cache HIT/MISS and scrape guard (Issue #12 / G12 demo).

Usage::

    docker compose up -d redis
    poetry run python scripts/verify_redis_cache.py
    poetry run python scripts/verify_redis_cache.py --ttl 2 --sleep 3
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from curanews.cache.feed_cache import CacheOutcome, FeedCache
from curanews.cache.redis_client import RedisClient
from curanews.cache.scrape_guard import ScrapeGuard
from curanews.config import get_settings
from curanews.logging_setup import setup_logging


def main() -> int:
    parser = argparse.ArgumentParser(description="Demonstrate Redis cache HIT/MISS and scrape guard.")
    parser.add_argument("--ttl", type=int, default=2, help="Feed cache TTL seconds for the demo.")
    parser.add_argument(
        "--sleep",
        type=float,
        default=None,
        help="Seconds to wait before the post-TTL lookup (defaults to ttl + 0.5).",
    )
    parser.add_argument("--user-id", default="demo-user-a")
    args = parser.parse_args()

    settings = get_settings()
    setup_logging(settings.log_level, app_name="curanews")

    client = RedisClient(settings.redis_url)
    cache = FeedCache(client=client, ttl_seconds=args.ttl)
    guard = ScrapeGuard(client=client)

    query = {"category": "tech", "limit": 5}
    payload = {"items": [{"title": "Redis cache demo headline", "score": 0.91}]}

    first = cache.get(args.user_id, query)
    cache.set(args.user_id, query, payload)
    second = cache.get(args.user_id, query)

    wait_seconds = args.sleep if args.sleep is not None else args.ttl + 0.5
    time.sleep(wait_seconds)
    third = cache.get(args.user_id, query)

    source_id = "example_news"
    lock_first = guard.try_acquire_lock(source_id, ttl_seconds=30)
    lock_second = guard.try_acquire_lock(source_id, ttl_seconds=30)
    guard.release_lock(source_id)
    guard.set_cooldown(source_id, ttl_seconds=30)
    on_cooldown = guard.is_on_cooldown(source_id)

    result = {
        "redis_available": client.available,
        "redis_url": settings.redis_url,
        "feed_cache_ttl_seconds": args.ttl,
        "cache_key": first.key,
        "lookups": [
            {"step": "initial", "outcome": first.outcome.value},
            {"step": "after_set", "outcome": second.outcome.value, "payload": second.payload},
            {"step": "after_ttl_wait", "outcome": third.outcome.value, "wait_seconds": wait_seconds},
        ],
        "scrape_guard": {
            "lock_first": lock_first,
            "lock_second": lock_second,
            "on_cooldown": on_cooldown,
        },
    }
    print(json.dumps(result, indent=2))

    if not client.available:
        print("redis unavailable — start with: docker compose up -d redis", file=sys.stderr)
        return 1

    expected = (
        first.outcome == CacheOutcome.MISS
        and second.outcome == CacheOutcome.HIT
        and third.outcome == CacheOutcome.MISS
        and lock_first is True
        and lock_second is False
        and on_cooldown is True
    )
    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
