"""Scrapy settings for CuraNews (Issues #4–#5)."""

from pathlib import Path

BOT_NAME = "curanews"

SPIDER_MODULES: list[str] = ["curanews.scrapers.spiders"]
NEWSPIDER_MODULE = "curanews.scrapers.spiders"

ROBOTSTXT_OBEY = True

CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1.0

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en,tr;q=0.9",
    "User-Agent": "CuraNewsBot/0.1 (+https://github.com/Faruk-T/CuraNews_Aggregator)",
}

# Issue #5 — post-process then persist
ITEM_PIPELINES = {
    "curanews.scrapers.pipelines.NewsItemCleaningPipeline": 100,
    "curanews.scrapers.pipelines.NewsItemValidationPipeline": 200,
    "curanews.scrapers.pipelines.NewsItemDeduplicationPipeline": 300,
    "curanews.scrapers.pipelines.SqlitePersistPipeline": 400,
}

SQLITE_PATH = str(Path("data/local/curanews.sqlite3"))

LOG_LEVEL = "INFO"
