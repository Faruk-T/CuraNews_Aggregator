"""Named adapter registry for CLI and orchestration."""

from __future__ import annotations

from curanews.scrapers.adapters.base import SourceAdapter
from curanews.scrapers.adapters.dynamic_fixture import DynamicFixtureAdapter
from curanews.scrapers.adapters.news_api_client import NewsApiAdapter
from curanews.scrapers.adapters.rss_client import RssCatalogAdapter
from curanews.scrapers.adapters.static_fixture import StaticFixtureAdapter

_BUILTIN: dict[str, type] = {
    "rss": RssCatalogAdapter,
    "static": StaticFixtureAdapter,
    "dynamic": DynamicFixtureAdapter,
    "api": NewsApiAdapter,
    "gnews": NewsApiAdapter,
    "example_news": StaticFixtureAdapter,
}


def list_adapters() -> tuple[str, ...]:
    return tuple(sorted(_BUILTIN))


def get_adapter(name: str) -> SourceAdapter:
    key = name.strip().lower()
    try:
        factory = _BUILTIN[key]
    except KeyError as exc:
        known = ", ".join(list_adapters())
        raise KeyError(f"Unknown adapter {name!r}. Choose from: {known}") from exc
    return factory()  # type: ignore[return-value]
