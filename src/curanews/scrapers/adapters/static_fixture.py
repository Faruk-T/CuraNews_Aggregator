"""Static HTML listing adapter (Issue #8 / G8)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from curanews.domain.models import RawArticleDraft
from curanews.scrapers.adapters._paths import fixture_path
from curanews.scrapers.parse_bs4 import parse_example_listing


class StaticFixtureAdapter:
    """Parse the Day 4 demo listing HTML via BeautifulSoup."""

    source_id = "example_news"
    kind: Literal["static"] = "static"

    def __init__(self, html_path: Path | None = None) -> None:
        self._html_path = html_path

    def fetch(self, *, limit: int = 50) -> list[RawArticleDraft]:
        path = self._resolve_fixture()
        html = path.read_text(encoding="utf-8")
        entries = parse_example_listing(
            html,
            base_url="https://example.com/",
            source=self.source_id,
        )
        return [
            RawArticleDraft(
                title=e.title,
                url=e.url,
                content=e.summary,
                summary=e.summary,
                published_date=e.published_date,
                source=e.source,
                category=e.category,
            )
            for e in entries[:limit]
        ]

    def _resolve_fixture(self) -> Path:
        if self._html_path and self._html_path.is_file():
            return self._html_path
        candidate = fixture_path("tests", "fixtures", "example_news_listing.html")
        if candidate.is_file():
            return candidate
        raise FileNotFoundError("example_news_listing.html fixture missing")
