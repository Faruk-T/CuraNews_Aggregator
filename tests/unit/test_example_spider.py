"""Unit tests for ExampleNewsSpider parse path."""

from pathlib import Path

from scrapy.http import HtmlResponse, Request

from curanews.scrapers.spiders.example_news import ExampleNewsSpider

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "example_news_listing.html"


def test_example_spider_yields_complete_news_items():
    html = FIXTURE.read_text(encoding="utf-8")
    spider = ExampleNewsSpider()
    request = Request(url="https://example.com/")
    response = HtmlResponse(
        url="https://example.com/",
        request=request,
        body=html.encode("utf-8"),
        encoding="utf-8",
    )

    items = list(spider.parse(response))
    assert len(items) == 4
    first = items[0]
    for field in (
        "article_id",
        "title",
        "url",
        "content",
        "published_date",
        "source",
        "category",
    ):
        assert first.get(field), f"missing {field}"
    assert first["source"] == "example_news"
    assert "Markets rally" in first["title"]


def test_example_spider_default_start_url_is_fixture():
    spider = ExampleNewsSpider()
    assert len(spider.start_urls) == 1
    assert spider.start_urls[0].startswith("file:")
