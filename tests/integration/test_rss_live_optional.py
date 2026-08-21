"""Optional live RSS fetch (skipped unless CURANEWS_LIVE_RSS=1)."""

from __future__ import annotations

import os

import pytest

from curanews.scrapers.adapters.rss_catalog import DEFAULT_RSS_FEEDS
from curanews.scrapers.adapters.rss_client import RssCatalogAdapter
from curanews.scrapers.validators import IncompleteNewsItemError, promote_draft


@pytest.mark.network
def test_live_bbc_world_rss_promotes_at_least_one_article() -> None:
    if os.getenv("CURANEWS_LIVE_RSS") != "1":
        pytest.skip("set CURANEWS_LIVE_RSS=1 to hit public RSS endpoints")

    bbc = next(feed for feed in DEFAULT_RSS_FEEDS if feed.key == "bbc_world")
    adapter = RssCatalogAdapter(feeds=(bbc,))
    drafts = adapter.fetch(limit=5)
    assert drafts, "BBC World RSS returned no items"

    promoted = 0
    for draft in drafts:
        try:
            article = promote_draft(draft)
        except IncompleteNewsItemError:
            continue
        assert article.url.host
        assert article.title
        promoted += 1
    assert promoted >= 1
