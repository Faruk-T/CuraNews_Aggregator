"""Scrapy settings for CuraNews (Issue #4 — polite crawl defaults)."""

BOT_NAME = "curanews"

SPIDER_MODULES: list[str] = ["curanews.scrapers.spiders"]
NEWSPIDER_MODULE = "curanews.scrapers.spiders"

ROBOTSTXT_OBEY = True

CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1.0

# AutoThrottle: adapt request rate to server response latency (Issue #4)
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

ITEM_PIPELINES = {
    "curanews.scrapers.pipelines.NewsItemValidationPipeline": 100,
}

LOG_LEVEL = "INFO"
