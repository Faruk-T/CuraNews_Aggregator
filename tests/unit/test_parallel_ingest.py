"""Tests for Issue #9 parallel asyncio ingestion."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Literal

from curanews.domain.models import RawArticleDraft
from curanews.scrapers.parallel import ingest_adapters_parallel_sync


class _SlowFakeAdapter:
    """Sleeps briefly to make parallel wall-clock gains measurable."""

    def __init__(self, source_id: str, delay: float = 0.15) -> None:
        self.source_id = source_id
        self.kind: Literal["static"] = "static"
        self._delay = delay

    def fetch(self, *, limit: int = 50) -> list[RawArticleDraft]:
        time.sleep(self._delay)
        return [
            RawArticleDraft(
                title=f"Headline from {self.source_id}",
                url=f"https://example.com/{self.source_id}/1",
                content=f"Body from {self.source_id}",
                summary=f"Summary {self.source_id}",
                published_date=datetime(2026, 8, 6, tzinfo=timezone.utc),
                source=self.source_id,
                category="test",
                author="Parallel Tester",
                language="en",
                metadata={"provider": "unit_test"},
            )
        ][:limit]


def test_parallel_ingest_faster_than_sequential_estimate() -> None:
    adapters = [
        _SlowFakeAdapter("alpha", delay=0.2),
        _SlowFakeAdapter("beta", delay=0.2),
        _SlowFakeAdapter("gamma", delay=0.2),
    ]
    summary = ingest_adapters_parallel_sync(adapters, limit=5, concurrency=3)

    assert summary.ok_count == 3
    assert summary.article_count == 3
    assert summary.concurrency == 3
    # Parallel wall time should beat the sum of per-task sleeps.
    assert summary.wall_seconds < summary.sequential_estimate_seconds * 0.85
    assert summary.wall_seconds < 0.5


def test_parallel_respects_concurrency_cap() -> None:
    adapters = [_SlowFakeAdapter(f"src{i}", delay=0.12) for i in range(4)]
    summary = ingest_adapters_parallel_sync(adapters, limit=1, concurrency=2)

    assert summary.ok_count == 4
    assert summary.concurrency == 2
    # With 4 tasks of ~0.12s and concurrency 2, wall should exceed one wave.
    assert summary.wall_seconds >= 0.2
    assert summary.wall_seconds < summary.sequential_estimate_seconds * 0.9


def test_parallel_continues_when_one_adapter_fails() -> None:
    class _Boom:
        source_id = "boom"
        kind: Literal["api"] = "api"

        def fetch(self, *, limit: int = 50) -> list[RawArticleDraft]:
            raise RuntimeError("simulated source outage")

    adapters = [_Boom(), _SlowFakeAdapter("ok", delay=0.05)]
    summary = ingest_adapters_parallel_sync(adapters, limit=1, concurrency=2)

    assert summary.ok_count == 1
    assert summary.article_count == 1
    assert summary.results[0].error is not None
    assert summary.results[1].ok
