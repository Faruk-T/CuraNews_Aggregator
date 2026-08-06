"""Map listing rows and API rows to fully populated drafts."""

from __future__ import annotations

from curanews.domain.models import RawArticleDraft
from curanews.scrapers.parse_bs4 import ListingEntry


def draft_from_listing_entry(entry: ListingEntry) -> RawArticleDraft:
    """Build a draft with optional enrichment fields filled when present."""
    content = entry.body or entry.summary or entry.title
    return RawArticleDraft(
        title=entry.title,
        url=entry.url,
        content=content,
        summary=entry.summary or content[:500],
        published_date=entry.published_date,
        source=entry.source,
        category=entry.category,
        author=entry.author,
        language=entry.language,
        metadata=dict(entry.metadata),
    )


def draft_from_listing_entries(entries: list[ListingEntry], *, limit: int) -> list[RawArticleDraft]:
    return [draft_from_listing_entry(e) for e in entries[:limit]]
