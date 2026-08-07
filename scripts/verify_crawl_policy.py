"""Verify crawl allowlist policy (Issue #10 / G10 demo).

Usage::

    poetry run python scripts/verify_crawl_policy.py
"""

from __future__ import annotations

import json
import sys

from curanews.scrapers.policy import (
    HostNotAllowedError,
    allowed_hosts,
    assert_url_allowed,
    default_concurrency,
    user_agent,
)


def main() -> int:
    samples = [
        ("https://example.com/news/1", True),
        ("file:///tmp/fixture.html", True),
        ("https://evil-scraper-target.test/x", False),
    ]
    rows: list[dict] = []
    for url, should_pass in samples:
        try:
            assert_url_allowed(url)
            ok = True
            error = None
        except HostNotAllowedError as exc:
            ok = False
            error = str(exc)
        rows.append(
            {
                "url": url,
                "expected_ok": should_pass,
                "actual_ok": ok,
                "error": error,
            }
        )

    payload = {
        "user_agent": user_agent(),
        "default_concurrency": default_concurrency(),
        "allowlist_hosts": sorted(allowed_hosts()),
        "checks": rows,
    }
    print(json.dumps(payload, indent=2))
    failed = [r for r in rows if r["expected_ok"] != r["actual_ok"]]
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
