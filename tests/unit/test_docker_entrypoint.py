"""Unit tests for Docker entrypoint helpers (Issue #20 / G20)."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import OperationalError

from scripts.docker_entrypoint import wait_for_database


def test_wait_for_database_succeeds_on_first_connect(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    class _Conn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def execute(self, _stmt):
            return None

    class _Engine:
        def connect(self):
            calls["n"] += 1
            return _Conn()

        def dispose(self):
            return None

    monkeypatch.setattr("scripts.docker_entrypoint.create_engine", lambda *_a, **_k: _Engine())
    wait_for_database("postgresql+psycopg://x", timeout_seconds=2)
    assert calls["n"] == 1


def test_wait_for_database_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_a, **_k):
        raise OperationalError("stmt", {}, Exception("down"))

    monkeypatch.setattr("scripts.docker_entrypoint.create_engine", boom)
    monkeypatch.setattr("scripts.docker_entrypoint.time.sleep", lambda _s: None)
    with pytest.raises(SystemExit, match="database not ready"):
        wait_for_database("postgresql+psycopg://x", timeout_seconds=0.01)
