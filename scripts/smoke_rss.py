"""One-shot live RSS catalog smoke (operator helper)."""

from __future__ import annotations

import json
import sys

from curanews.config import get_settings
from curanews.scrapers.adapters.rss_catalog import DEFAULT_RSS_FEEDS
from curanews.scrapers.adapters.rss_client import RssCatalogAdapter
from curanews.scrapers.policy import allowed_hosts


def main() -> int:
    get_settings.cache_clear()
    allowed_hosts.cache_clear()
    results = []
    for feed in DEFAULT_RSS_FEEDS:
        row = {"key": feed.key, "n": 0, "sample": "", "error": ""}
        try:
            drafts = RssCatalogAdapter(feeds=(feed,)).fetch(limit=2)
            row["n"] = len(drafts)
            row["sample"] = drafts[0].title if drafts else "EMPTY"
        except Exception as exc:  # noqa: BLE001
            row["error"] = str(exc)
        results.append(row)
        print(f"{row['key']}\t{row['n']}\t{row['sample'] or row['error']}", flush=True)
    print(json.dumps(results, ensure_ascii=False, indent=2), flush=True)
    return 0 if all(r["n"] > 0 for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
