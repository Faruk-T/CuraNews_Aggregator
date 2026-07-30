"""Tests for Scrapy polite-crawl settings (Issue #4)."""

from scrapy.utils.project import get_project_settings


def test_autothrottle_and_download_delay_enabled():
    settings = get_project_settings()
    assert settings.getbool("AUTOTHROTTLE_ENABLED") is True
    assert settings.getfloat("DOWNLOAD_DELAY") >= 1.0
    assert settings.getint("CONCURRENT_REQUESTS") <= 2
    assert settings.getbool("ROBOTSTXT_OBEY") is True
