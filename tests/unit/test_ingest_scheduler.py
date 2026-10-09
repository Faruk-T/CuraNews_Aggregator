from __future__ import annotations

from types import SimpleNamespace

from curanews.ingestion.scheduler import IngestScheduler, scheduler_interval_seconds


class _FakeGuard:
    def __init__(self, *, cooldown: bool = False, lock: bool = True) -> None:
        self.cooldown = cooldown
        self.lock = lock
        self.cooldowns: list[int] = []
        self.released = 0

    def is_on_cooldown(self, _key: str) -> bool:
        return self.cooldown

    def try_acquire_lock(self, _key: str, *, ttl_seconds: int) -> bool:
        del ttl_seconds
        return self.lock

    def set_cooldown(self, _key: str, *, ttl_seconds: int) -> bool:
        self.cooldowns.append(ttl_seconds)
        return True

    def release_lock(self, _key: str) -> bool:
        self.released += 1
        return True


def test_scheduler_disabled_when_interval_is_zero() -> None:
    settings = SimpleNamespace(ingest_interval_minutes=0, is_prod=False)
    scheduler = IngestScheduler(scheduler_interval_seconds(settings))
    assert not scheduler.enabled
    scheduler.start()
    assert scheduler._thread is None


def test_prod_default_interval_is_ten_minutes(monkeypatch) -> None:
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    settings = SimpleNamespace(ingest_interval_minutes=0, is_prod=True)
    assert scheduler_interval_seconds(settings) == 600


def test_pytest_does_not_enable_prod_default(monkeypatch) -> None:
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/unit/test_ingest_scheduler.py")
    settings = SimpleNamespace(ingest_interval_minutes=0, is_prod=True)
    assert scheduler_interval_seconds(settings) == 0


def test_tick_skips_when_cooling_down() -> None:
    scheduler = IngestScheduler(600, runner=lambda: 0, guard=_FakeGuard(cooldown=True))
    assert scheduler.tick() == "cooldown"


def test_tick_skips_when_lock_busy() -> None:
    scheduler = IngestScheduler(600, runner=lambda: 0, guard=_FakeGuard(lock=False))
    assert scheduler.tick() == "busy"


def test_tick_runs_and_releases_lock() -> None:
    guard = _FakeGuard()
    scheduler = IngestScheduler(600, runner=lambda: 0, guard=guard)
    assert scheduler.tick() == "ran"
    assert guard.released == 1
    assert guard.cooldowns == [570]


def test_failed_tick_uses_shorter_cooldown() -> None:
    guard = _FakeGuard()
    scheduler = IngestScheduler(600, runner=lambda: 1, guard=guard)
    assert scheduler.tick() == "failed"
    assert guard.cooldowns == [90]
