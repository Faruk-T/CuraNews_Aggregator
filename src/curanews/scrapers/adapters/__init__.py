"""Unified source adapters (Issue #8 / G8)."""

from curanews.scrapers.adapters.base import SourceAdapter, adapter_label
from curanews.scrapers.adapters.consumer import ingest_from_adapter
from curanews.scrapers.adapters.dynamic_fixture import DynamicFixtureAdapter
from curanews.scrapers.adapters.news_api import load_gnews_fixture, parse_gnews_payload
from curanews.scrapers.adapters.news_api_client import NewsApiAdapter
from curanews.scrapers.adapters.registry import get_adapter, list_adapters
from curanews.scrapers.adapters.rss import load_rss_fixture, parse_feed_xml
from curanews.scrapers.adapters.rss_client import RssCatalogAdapter
from curanews.scrapers.adapters.static_fixture import StaticFixtureAdapter

__all__ = [
    "DynamicFixtureAdapter",
    "NewsApiAdapter",
    "RssCatalogAdapter",
    "SourceAdapter",
    "StaticFixtureAdapter",
    "adapter_label",
    "get_adapter",
    "ingest_from_adapter",
    "list_adapters",
    "load_gnews_fixture",
    "load_rss_fixture",
    "parse_feed_xml",
    "parse_gnews_payload",
]
