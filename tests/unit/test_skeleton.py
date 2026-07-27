"""Smoke test for Day 1 package skeleton."""

from curanews import __version__
from curanews.__main__ import main


def test_version_is_semver_like():
    assert __version__ == "0.1.0"


def test_main_prints_skeleton_ok(capsys):
    main()
    out = capsys.readouterr().out
    assert "skeleton OK" in out
    assert "curanews" in out
