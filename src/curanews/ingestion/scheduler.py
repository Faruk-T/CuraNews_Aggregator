"""Background RSS refresh loop owned by the API process.

Each tick spawns ``python -m curanews.ingestion.refresh`` so parsing and NLP
run outside the web server's interpreter. A Redis lock plus cooldown keeps
several uvicorn workers (or a manual run) from refreshing at the same time.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
from collections.abc import Callable

from curanews.cache.scrape_guard import ScrapeGuard
from curanews.config import Settings

logger = logging.getLogger(__name__)

GUARD_KEY = "rss_refresh"
RUN_TIMEOUT_SECONDS = 20 * 60
FIRST_TICK_DELAY_SECONDS = 5.0
PROD_DEFAULT_INTERVAL_MINUTES = 10
REFRESH_COMMAND = (sys.executable, "-m", "curanews.ingestion.refresh")

Runner = Callable[[], int]


def scheduler_interval_seconds(settings: Settings) -> float:
    """Production enables a 10-minute loop when the env var is omitted.

    Tests stay off (interval 0) even if ``APP_ENV=prod`` is in a local ``.env``.
    """
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return 0.0
    minutes = settings.ingest_interval_minutes
    if minutes > 0:
        return float(minutes * 60)
    if settings.is_prod:
        return float(PROD_DEFAULT_INTERVAL_MINUTES * 60)
    return 0.0


def run_refresh_subprocess() -> int:
    try:
        completed = subprocess.run(REFRESH_COMMAND, timeout=RUN_TIMEOUT_SECONDS, check=False)
    except subprocess.TimeoutExpired:
        logger.error("rss refresh timed out after %ss", RUN_TIMEOUT_SECONDS)
        return -1
    return completed.returncode


class IngestScheduler:
    def __init__(
        self,
        interval_seconds: float,
        *,
        runner: Runner = run_refresh_subprocess,
        guard: ScrapeGuard | None = None,
    ) -> None:
        self.interval_seconds = interval_seconds
        self._runner = runner
        self._guard = guard
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @classmethod
    def from_settings(cls, settings: Settings) -> IngestScheduler:
        return cls(scheduler_interval_seconds(settings))

    @property
    def enabled(self) -> bool:
        return self.interval_seconds > 0

    def start(self) -> None:
        if not self.enabled or self._thread is not None:
            return
        self._thread = threading.Thread(target=self._loop, name="rss-refresh", daemon=True)
        self._thread.start()
        logger.info("rss refresh scheduler started interval=%ss", self.interval_seconds)

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout)
            self._thread = None

    def _loop(self) -> None:
        delay = min(FIRST_TICK_DELAY_SECONDS, self.interval_seconds)
        while not self._stop.wait(delay):
            try:
                self.tick()
            except Exception:  # noqa: BLE001
                logger.exception("rss refresh tick crashed")
            delay = self.interval_seconds

    def tick(self) -> str:
        guard = self._guard or ScrapeGuard()
        if guard.is_on_cooldown(GUARD_KEY):
            return "cooldown"
        if not guard.try_acquire_lock(GUARD_KEY, ttl_seconds=RUN_TIMEOUT_SECONDS + 60):
            return "busy"
        code = -1
        try:
            code = self._runner()
        finally:
            cool = (
                max(30, int(self.interval_seconds) - 30)
                if code == 0
                else min(90, max(30, int(self.interval_seconds) // 4 or 30))
            )
            guard.set_cooldown(GUARD_KEY, ttl_seconds=cool)
            guard.release_lock(GUARD_KEY)
        logger.info("rss refresh finished exit_code=%s", code)
        return "ran" if code == 0 else "failed"
