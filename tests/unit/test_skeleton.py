"""Smoke test for package CLI entrypoint."""

from curanews import __version__
from curanews.__main__ import main


def test_version_is_semver_like():
    assert __version__ == "0.1.0"


def test_main_prints_ready(capsys):
    main()
    out = capsys.readouterr().out
    assert "ready" in out
    assert "curanews" in out.lower()
