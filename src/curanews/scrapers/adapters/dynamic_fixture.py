"""Dynamic Playwright listing adapter (Issue #8 / G8)."""

from __future__ import annotations

import asyncio
from typing import Literal

from curanews.browser.dynamic_listing import fetch_dynamic_listing, fixture_file_url
from curanews.domain.models import RawArticleDraft


class DynamicFixtureAdapter:
    """Scroll the offline infinite-scroll fixture and return drafts."""

    source_id = "dynamic_demo"
    kind: Literal["dynamic"] = "dynamic"

    def fetch(self, *, limit: int = 50) -> list[RawArticleDraft]:
        url = fixture_file_url()
        entries, _scroll = asyncio.run(
            fetch_dynamic_listing(
                url,
                source=self.source_id,
                base_url="https://example.com/",
                min_items=min(limit, 4),
            )
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
