"""Tests for text cleaning helpers."""

from curanews.ingestion.cleaning import clean_news_payload, collapse_whitespace


def test_collapse_whitespace():
    assert collapse_whitespace("  hello   world\n") == "hello world"


def test_clean_news_payload_normalizes_category_and_title():
    payload = {
        "title": "  Markets   rally  ",
        "content": "body",
        "category": "Personal Finance",
        "url": " https://example.com/a ",
        "source": " ExampleNews ",
    }
    cleaned = clean_news_payload(payload)
    assert cleaned["title"] == "Markets rally"
    assert cleaned["category"] == "personal-finance"
    assert cleaned["url"] == "https://example.com/a"
    assert cleaned["source"] == "ExampleNews"
