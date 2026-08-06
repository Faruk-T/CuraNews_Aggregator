"""Tests for Issue #8 source adapters and shared ingestion."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import pytest

from curanews.domain.models import RawArticleDraft
from curanews.scrapers.adapters import (
    get_adapter,
    ingest_from_adapter,
    list_adapters,
    load_gnews_fixture,
    parse_gnews_payload,
)
from curanews.scrapers.adapters.static_fixture import StaticFixtureAdapter

FIXTURE_JSON = Path(__file__).resolve().parent / "fixtures" / "gnews_sample.json"


class FakeAdapter:
    """Minimal adapter for consumer tests (G8 acceptance)."""

    source_id = "fake_unit"
    kind: Literal["static"] = "static"

    def fetch(self, *, limit: int = 50) -> list[RawArticleDraft]:
        return [
            RawArticleDraft(
                title="Fake headline",
                url="https://example.com/fake/1",
                content="Body text for fake adapter.",
                published_date=datetime(2026, 8, 6, tzinfo=timezone.utc),
                source="fake_unit",
                category="test",
            )
        ][:limit]


def test_ingest_from_adapter_works_for_fake_and_static() -> None:
    fake_articles = ingest_from_adapter(FakeAdapter(), limit=5)
    assert len(fake_articles) == 1
    assert fake_articles[0].title == "Fake headline"

    static_articles = ingest_from_adapter(StaticFixtureAdapter(), limit=5)
    assert len(static_articles) >= 1


def test_parse_gnews_fixture_file() -> None:
    drafts = load_gnews_fixture(FIXTURE_JSON)
    assert len(drafts) == 2
    assert drafts[0].title.startswith("Fixture headline")


def test_parse_gnews_payload_skips_incomplete_rows() -> None:
    payload = {
        "articles": [
            {"title": "OK", "url": "https://example.com/a", "content": "body"},
            {"title": "", "url": "https://example.com/b"},
        ]
    }
    drafts = parse_gnews_payload(payload, default_category="world")
    assert len(drafts) == 1
    assert drafts[0].category == "world"


def test_registry_lists_builtin_adapters() -> None:
    names = list_adapters()
    assert "static" in names
    assert "dynamic" in names
    assert get_adapter("static").kind == "static"


def test_news_api_adapter_offline_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEWS_API_KEY", "")
    from curanews.config import get_settings

    get_settings.cache_clear()
    adapter = get_adapter("api")
    drafts = adapter.fetch(limit=5)
    get_settings.cache_clear()
    assert len(drafts) >= 1
