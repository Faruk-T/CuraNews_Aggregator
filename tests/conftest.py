# Package path bootstrap for local runs without install.

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "unit: fast isolated unit tests")
    config.addinivalue_line(
        "markers",
        "integration: cross-module tests (API TestClient, ingestion, curation)",
    )
    config.addinivalue_line(
        "markers",
        "redis: optional live Redis tests (set CURANEWS_REDIS_URL)",
    )
    config.addinivalue_line(
        "markers",
        "network: optional tests that hit the public internet (set CURANEWS_LIVE_RSS=1)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-mark by path and skip optional live/network tests by default."""
    redis_url = os.getenv("CURANEWS_REDIS_URL") or os.getenv("REDIS_URL")
    skip_redis = pytest.mark.skip(reason="set CURANEWS_REDIS_URL to run live Redis tests")
    skip_network = pytest.mark.skip(reason="set CURANEWS_LIVE_RSS=1 to hit public RSS feeds")

    for item in items:
        path = str(getattr(item, "path", item.fspath)).replace("\\", "/")
        if "/tests/integration/" in path:
            item.add_marker(pytest.mark.integration)
        elif "/tests/unit/" in path or path.endswith("/tests/test_source_adapters.py"):
            item.add_marker(pytest.mark.unit)

        if item.get_closest_marker("redis") is not None and not redis_url:
            item.add_marker(skip_redis)
        if item.get_closest_marker("network") is not None and os.getenv("CURANEWS_LIVE_RSS") != "1":
            item.add_marker(skip_network)
