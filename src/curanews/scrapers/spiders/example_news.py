"""First static listing spider (Issue #4).

By default crawls the bundled HTML fixture so demos work offline.
Pass ``-a start_url=https://...`` to target a live listing that matches
the expected ``article.news-card`` markup (or extend the parser later).
"""

from __future__ import annotations

from pathlib import Path

import scrapy

from curanews.scrapers.parse_bs4 import parse_example_listing
from curanews.scrapers.spiders.base import BaseNewsSpider


def _default_fixture_path() -> Path:
    candidates = [
        Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "example_news_listing.html",
        Path.cwd() / "tests" / "fixtures" / "example_news_listing.html",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return candidates[0]


class ExampleNewsSpider(BaseNewsSpider):
    """Extract titles, links, and listing metadata into ``NewsItem`` rows."""

    name = "example_news"
    source_key = "example_news"
    allowed_domains: list[str] = []

    def __init__(self, start_url: str | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if start_url:
            self.start_urls = [start_url]
        else:
            fixture = _default_fixture_path()
            if not fixture.is_file():
                raise FileNotFoundError(f"Demo fixture missing: {fixture}")
            self.start_urls = [self.path_to_file_url(fixture)]

    def parse(self, response: scrapy.http.Response, **kwargs):
        base_url = response.url
        # file:// listings use absolute-path hrefs; join against a stable https base
        if base_url.startswith("file:"):
            base_url = "https://example.com/"
        entries = parse_example_listing(
            response.text,
            base_url=base_url,
            source=self.source_key,
        )
        self.logger.info("parsed %s listing entries from %s", len(entries), response.url)
        for entry in entries:
            yield self.build_news_item(
                title=entry.title,
                url=entry.url,
                content=entry.summary,
                published_date=entry.published_date,
                category=entry.category,
                summary=entry.summary,
            )
