"""Scrapy settings for the CuraNews crawler package (skeleton — Issue #3/#4)."""

BOT_NAME = "curanews"

SPIDER_MODULES: list[str] = ["curanews.scrapers.spiders"]
NEWSPIDER_MODULE = "curanews.scrapers.spiders"

# Obey robots.txt by default (polite crawling — reinforced in later issues)
ROBOTSTXT_OBEY = True

# Keep concurrency low during internship demos
CONCURRENT_REQUESTS = 2
DOWNLOAD_DELAY = 0.5

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en,tr;q=0.9",
    "User-Agent": "CuraNewsBot/0.1 (+https://github.com/Faruk-T/CuraNews_Aggregator)",
}

ITEM_PIPELINES = {
    "curanews.scrapers.pipelines.NewsItemValidationPipeline": 100,
}

LOG_LEVEL = "INFO"
