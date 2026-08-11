"""Redis caching layer — Issue #12 / G12."""

from curanews.cache.feed_cache import CacheOutcome, FeedCache, FeedCacheResult, feed_cache_key
from curanews.cache.redis_client import RedisClient, get_redis_client
from curanews.cache.scrape_guard import ScrapeGuard, scrape_cooldown_key, scrape_lock_key

__all__ = [
    "CacheOutcome",
    "FeedCache",
    "FeedCacheResult",
    "RedisClient",
    "ScrapeGuard",
    "feed_cache_key",
    "get_redis_client",
    "scrape_cooldown_key",
    "scrape_lock_key",
]
