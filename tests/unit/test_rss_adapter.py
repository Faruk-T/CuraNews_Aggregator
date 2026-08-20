"""RSS 2.0 / Atom catalog adapter tests (real news path, offline)."""

from __future__ import annotations

from pathlib import Path

import pytest

from curanews.config import Settings
from curanews.scrapers.adapters import get_adapter, list_adapters, load_rss_fixture, parse_feed_xml
from curanews.scrapers.adapters.rss_catalog import DEFAULT_RSS_FEEDS, RSS_ALLOWLIST_HOSTS, RssFeed
from curanews.scrapers.adapters.rss_client import RssCatalogAdapter
from curanews.scrapers.policy import is_url_allowed
from curanews.scrapers.validators import promote_draft

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "rss_sample.xml"


def test_parse_rss_fixture_skips_incomplete_and_promotes() -> None:
    drafts = load_rss_fixture()
    assert len(drafts) == 2
    titles = {d.title for d in drafts}
    assert "Fixture: coalition agrees ceasefire timetable" in titles
    assert "Incomplete row without a permalink" not in titles

    first = promote_draft(drafts[0])
    assert first.source.startswith("fixture_wire:")
    assert first.language == "en"
    assert first.metadata["provider"] == "rss"
    assert "Geneva" in first.content
    assert first.author


def test_parse_atom_entry() -> None:
    atom = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Atom fixture headline</title>
        <link rel="alternate" href="https://www.theguardian.com/world/atom-fixture"/>
        <published>2026-08-19T09:00:00Z</published>
        <summary>Atom summary body for CuraNews parser.</summary>
        <author><name>Atom Desk</name></author>
      </entry>
    </feed>
    """
    feed = RssFeed(
        key="guardian_world",
        publisher="The Guardian",
        url="https://www.theguardian.com/world/rss",
        category="world",
        language="en",
        host="www.theguardian.com",
    )
    drafts = parse_feed_xml(atom, feed=feed)
    assert len(drafts) == 1
    assert drafts[0].url == "https://www.theguardian.com/world/atom-fixture"
    assert drafts[0].author == "Atom Desk"


def test_rss_adapter_uses_injected_http_not_network() -> None:
    xml = FIXTURE.read_text(encoding="utf-8")
    calls: list[str] = []

    def fake_get(url: str) -> str:
        calls.append(url)
        return xml

    feed = DEFAULT_RSS_FEEDS[0]
    adapter = RssCatalogAdapter(feeds=(feed,), http_get=fake_get)
    drafts = adapter.fetch(limit=10)
    assert calls == [feed.url]
    assert len(drafts) == 2
    assert adapter.kind == "rss"
    assert adapter.source_id == "rss_catalog"


def test_fetch_round_robins_publishers_instead_of_filling_from_first() -> None:
    xml = FIXTURE.read_text(encoding="utf-8")
    bbc, guardian = DEFAULT_RSS_FEEDS[0], DEFAULT_RSS_FEEDS[2]
    adapter = RssCatalogAdapter(feeds=(bbc, guardian), http_get=lambda _url: xml)
    drafts = adapter.fetch(limit=4)
    publishers = [d.metadata["publisher"] for d in drafts]
    assert publishers.count("BBC News") == 2
    assert publishers.count("The Guardian") == 2
    assert publishers[0] != publishers[1]


def test_parse_rss_ignores_comments_without_crashing() -> None:
    xml = """<?xml version="1.0"?><rss version="2.0"><channel>
    <!-- comment -->
    <item><title>Comment-safe</title><link>https://www.trthaber.com/a</link>
    <description>ok</description></item>
    </channel></rss>"""
    feed = DEFAULT_RSS_FEEDS[0]
    drafts = parse_feed_xml(xml, feed=feed)
    assert len(drafts) == 1
    assert drafts[0].title == "Comment-safe"

    adapter = RssCatalogAdapter(use_fixture=True)
    drafts = adapter.fetch(limit=1)
    assert len(drafts) == 1


def test_registry_includes_rss() -> None:
    assert "rss" in list_adapters()
    assert get_adapter("rss").kind == "rss"


def test_default_allowlist_covers_every_catalog_host(monkeypatch: pytest.MonkeyPatch) -> None:
    default = Settings.model_fields["scrape_allowlist_hosts"].default
    assert isinstance(default, str)
    allowed = {part.strip() for part in default.split(",") if part.strip()}
    missing = set(RSS_ALLOWLIST_HOSTS) - allowed
    assert not missing, f"RSS hosts missing from default allowlist: {missing}"

    monkeypatch.setenv("SCRAPE_ALLOWLIST_HOSTS", default)
    from curanews.config import get_settings
    from curanews.scrapers import policy as policy_mod

    get_settings.cache_clear()
    policy_mod.allowed_hosts.cache_clear()
    assert is_url_allowed(DEFAULT_RSS_FEEDS[0].url)
    get_settings.cache_clear()
    policy_mod.allowed_hosts.cache_clear()
