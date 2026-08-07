"""Tests for text cleaning helpers."""

from curanews.ingestion.cleaning import clean_news_payload, clean_raw_draft, collapse_whitespace, strip_html_tags


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


def test_strip_html_tags_from_content():
    raw = "<p>Hello <strong>world</strong></p>\n\n  extra "
    assert strip_html_tags(raw) == "Hello world extra"


def test_clean_raw_draft_strips_markup_before_promotion():
    from datetime import datetime, timezone

    from curanews.domain.models import RawArticleDraft
    from curanews.scrapers.validators import promote_draft

    draft = RawArticleDraft(
        title="Title",
        url="https://example.com/x",
        content="<div>Full <b>body</b></div>",
        summary="<i>Short</i>",
        published_date=datetime(2026, 8, 7, tzinfo=timezone.utc),
        source="example_news",
        category="tech",
    )
    cleaned = clean_raw_draft(draft)
    article = promote_draft(cleaned)
    assert article.content == "Full body"
    assert article.summary == "Short"
