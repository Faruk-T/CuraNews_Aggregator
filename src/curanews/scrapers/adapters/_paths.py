"""Resolve repo-root paths for offline fixtures."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    # src/curanews/scrapers/adapters/_paths.py → repo root
    return Path(__file__).resolve().parents[4]


def fixture_path(*parts: str) -> Path:
    return repo_root().joinpath(*parts)
