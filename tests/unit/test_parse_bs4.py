"""Unit tests for BeautifulSoup listing parser."""

from datetime import timezone
from pathlib import Path

from curanews.scrapers.parse_bs4 import iter_titles_and_links, parse_example_listing

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "example_news_listing.html"


def test_parse_example_listing_extracts_four_cards():
    html = FIXTURE.read_text(encoding="utf-8")
    entries = parse_example_listing(
        html,
        base_url="https://example.com/",
        source="example_news",
    )
    assert len(entries) == 4
    assert entries[0].title.startswith("Markets rally")
    assert entries[0].url == "https://example.com/news/markets-rally-on-rate-cut-hopes"
    assert entries[0].category == "economy"
    assert entries[0].published_date.tzinfo is not None
    assert entries[0].published_date.tzinfo.utcoffset(entries[0].published_date) == timezone.utc.utcoffset(
        entries[0].published_date
    )


def test_iter_titles_and_links():
    html = FIXTURE.read_text(encoding="utf-8")
    pairs = list(iter_titles_and_links(html, base_url="https://example.com/"))
    assert len(pairs) == 4
    assert all(title and url.startswith("https://") for title, url in pairs)
