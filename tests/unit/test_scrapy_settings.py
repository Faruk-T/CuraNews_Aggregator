"""Tests for Scrapy polite-crawl and pipeline settings (Issues #4–#5)."""

from scrapy.utils.project import get_project_settings


def test_autothrottle_and_download_delay_enabled():
    settings = get_project_settings()
    assert settings.getbool("AUTOTHROTTLE_ENABLED") is True
    assert settings.getfloat("DOWNLOAD_DELAY") >= 1.0
    assert settings.getint("CONCURRENT_REQUESTS") <= 2
    assert settings.getbool("ROBOTSTXT_OBEY") is True


def test_item_pipelines_include_sqlite_chain():
    settings = get_project_settings()
    pipelines = settings.getdict("ITEM_PIPELINES")
    assert "curanews.scrapers.pipelines.NewsItemCleaningPipeline" in pipelines
    assert "curanews.scrapers.pipelines.NewsItemDeduplicationPipeline" in pipelines
    assert "curanews.scrapers.pipelines.SqlitePersistPipeline" in pipelines
    assert settings.get("SQLITE_PATH")
