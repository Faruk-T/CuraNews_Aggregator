"""BeautifulSoup helpers for static HTML news listings (Issue #4)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup


@dataclass(frozen=True, slots=True)
class ListingEntry:
    """Parsed row from a static listing page."""

    title: str
    url: str
    summary: str
    category: str
    published_date: datetime
    source: str


def parse_example_listing(html: str, *, base_url: str, source: str) -> list[ListingEntry]:
    """Parse the Day 4 demo listing fixture / compatible markup.

    Expected structure::

        <article class="news-card" data-category="economy" data-published="2026-07-29T10:00:00+00:00">
          <a class="news-title" href="/news/1">Title</a>
          <p class="news-summary">...</p>
        </article>
    """
    soup = BeautifulSoup(html, "lxml")
    entries: list[ListingEntry] = []

    for card in soup.select("article.news-card"):
        anchor = card.select_one("a.news-title")
        if anchor is None:
            continue
        title = anchor.get_text(" ", strip=True)
        href = anchor.get("href") or ""
        if not title or not href:
            continue

        summary_el = card.select_one(".news-summary")
        summary = summary_el.get_text(" ", strip=True) if summary_el else title
        category = (card.get("data-category") or "general").strip().lower()
        published_raw = card.get("data-published")
        published_date = _parse_datetime(published_raw)

        entries.append(
            ListingEntry(
                title=title,
                url=urljoin(base_url, href),
                summary=summary or title,
                category=category or "general",
                published_date=published_date,
                source=source,
            )
        )

    return entries


def iter_titles_and_links(html: str, *, base_url: str) -> Iterable[tuple[str, str]]:
    """Yield ``(title, absolute_url)`` pairs for quick smoke checks."""
    for entry in parse_example_listing(html, base_url=base_url, source="unknown"):
        yield entry.title, entry.url


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    cleaned = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
