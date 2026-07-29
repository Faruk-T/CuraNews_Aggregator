"""Tests for Settings loading and defaults."""

from curanews.config import Settings, get_settings


def test_settings_defaults():
    settings = Settings()
    assert settings.app_env == "dev"
    assert settings.log_level == "INFO"
    assert settings.scrape_concurrency == 2
    assert settings.api_port == 8000


def test_settings_env_override(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("SCRAPE_CONCURRENCY", "1")
    settings = Settings()
    assert settings.app_env == "test"
    assert settings.log_level == "DEBUG"
    assert settings.scrape_concurrency == 1


def test_get_settings_is_cached(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("APP_ENV", "dev")
    first = get_settings()
    second = get_settings()
    assert first is second
    get_settings.cache_clear()
