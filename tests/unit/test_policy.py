"""Tests for host allowlist and polite defaults (Issue #10 / G10)."""

from __future__ import annotations

import pytest

from curanews.scrapers.policy import (
    HostNotAllowedError,
    assert_url_allowed,
    default_concurrency,
    is_url_allowed,
)


def test_default_concurrency_is_at_most_two() -> None:
    assert default_concurrency() <= 2


def test_allowlist_permits_example_and_file_fixtures() -> None:
    assert is_url_allowed("https://example.com/news/1")
    assert is_url_allowed("file:///C:/tmp/demo.html")


def test_allowlist_blocks_unknown_host() -> None:
    assert not is_url_allowed("https://evil-scraper-target.test/article")
    with pytest.raises(HostNotAllowedError):
        assert_url_allowed("https://evil-scraper-target.test/article")


def test_allowlist_respects_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCRAPE_ALLOWLIST_HOSTS", "example.com,demo.local")
    from curanews.config import get_settings
    from curanews.scrapers import policy as policy_mod

    get_settings.cache_clear()
    policy_mod.allowed_hosts.cache_clear()
    assert is_url_allowed("https://demo.local/page")
    assert not is_url_allowed("https://gnews.io/api/v4/top-headlines")
    get_settings.cache_clear()
    policy_mod.allowed_hosts.cache_clear()
