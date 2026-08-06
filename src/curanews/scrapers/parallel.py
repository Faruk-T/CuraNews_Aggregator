"""Parallel multi-source ingestion with asyncio (Issue #9)."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass

from curanews.config import get_settings
from curanews.domain.models import NewsArticle, RawArticleDraft
from curanews.scrapers.adapters.base import SourceAdapter, adapter_label
from curanews.scrapers.validators import IncompleteNewsItemError, promote_draft

logger = logging.getLogger("curanews.scrapers.parallel")


@dataclass(frozen=True, slots=True)
class AdapterFetchResult:
    """Per-adapter outcome from a parallel batch."""

    source_id: str
    kind: str
    drafts: tuple[RawArticleDraft, ...]
    articles: tuple[NewsArticle, ...]
    elapsed_seconds: float
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass(frozen=True, slots=True)
class ParallelIngestSummary:
    """Wall-clock timing for concurrent adapter fetches."""

    results: tuple[AdapterFetchResult, ...]
    wall_seconds: float
    concurrency: int

    @property
    def ok_count(self) -> int:
        return sum(1 for r in self.results if r.ok)

    @property
    def article_count(self) -> int:
        return sum(len(r.articles) for r in self.results if r.ok)

    @property
    def sequential_estimate_seconds(self) -> float:
        return sum(r.elapsed_seconds for r in self.results)


async def _fetch_one(
    adapter: SourceAdapter,
    *,
    limit: int,
    semaphore: asyncio.Semaphore,
) -> AdapterFetchResult:
    label = adapter_label(adapter)
    started = time.perf_counter()
    async with semaphore:
        try:
            drafts = await asyncio.to_thread(adapter.fetch, limit=limit)
            articles: list[NewsArticle] = []
            for draft in drafts:
                try:
                    articles.append(promote_draft(draft))
                except IncompleteNewsItemError:
                    continue
            elapsed = time.perf_counter() - started
            logger.info(
                "adapter_ok source=%s drafts=%s articles=%s elapsed=%.3fs",
                label,
                len(drafts),
                len(articles),
                elapsed,
            )
            return AdapterFetchResult(
                source_id=adapter.source_id,
                kind=adapter.kind,
                drafts=tuple(drafts),
                articles=tuple(articles),
                elapsed_seconds=elapsed,
            )
        except Exception as exc:  # noqa: BLE001
            elapsed = time.perf_counter() - started
            logger.warning("adapter_fail source=%s elapsed=%.3fs error=%s", label, elapsed, exc)
            return AdapterFetchResult(
                source_id=adapter.source_id,
                kind=adapter.kind,
                drafts=tuple(),
                articles=tuple(),
                elapsed_seconds=elapsed,
                error=str(exc),
            )


async def ingest_adapters_parallel(
    adapters: Sequence[SourceAdapter],
    *,
    limit: int = 50,
    concurrency: int | None = None,
) -> ParallelIngestSummary:
    """Fetch many ``SourceAdapter`` instances concurrently (thread offload).

    Sync adapter ``fetch()`` calls run in ``asyncio.to_thread`` so blocking
    I/O (httpx, file reads, Playwright ``asyncio.run`` wrappers) does not
    freeze the event loop. A semaphore caps active workers to
    ``SCRAPE_CONCURRENCY`` (default 2).
    """
    settings = get_settings()
    workers = max(1, concurrency or settings.scrape_concurrency)
    semaphore = asyncio.Semaphore(workers)
    wall_start = time.perf_counter()
    results = await asyncio.gather(
        *[_fetch_one(adapter, limit=limit, semaphore=semaphore) for adapter in adapters]
    )
    wall = time.perf_counter() - wall_start
    summary = ParallelIngestSummary(
        results=tuple(results),
        wall_seconds=wall,
        concurrency=workers,
    )
    logger.info(
        "parallel_ingest adapters=%s ok=%s articles=%s wall=%.3fs sequential_estimate=%.3fs concurrency=%s",
        len(adapters),
        summary.ok_count,
        summary.article_count,
        summary.wall_seconds,
        summary.sequential_estimate_seconds,
        workers,
    )
    return summary


def ingest_adapters_parallel_sync(
    adapters: Sequence[SourceAdapter],
    *,
    limit: int = 50,
    concurrency: int | None = None,
) -> ParallelIngestSummary:
    """Synchronous entry point for CLI scripts."""
    return asyncio.run(
        ingest_adapters_parallel(adapters, limit=limit, concurrency=concurrency)
    )
