"""Tests for SQLite article store and URL hashing."""

from curanews.db import SqliteArticleStore, canonical_url_hash


def test_canonical_url_hash_stable():
    assert canonical_url_hash("https://a.com/x") == canonical_url_hash("https://a.com/x")
    assert canonical_url_hash("https://a.com/x") != canonical_url_hash("https://a.com/y")


def test_sqlite_insert_and_dedupe(tmp_path):
    db_path = tmp_path / "test.sqlite3"
    store = SqliteArticleStore(db_path)
    payload = {
        "article_id": "id-1",
        "url": "https://example.com/news/1",
        "title": "Hello",
        "content": "Body text",
        "published_date": "2026-07-31T10:00:00+00:00",
        "source": "example_news",
        "category": "tech",
        "summary": "Body text",
        "author": None,
        "scraped_at": "2026-07-31T12:00:00+00:00",
        "metadata": {"spider": "example_news"},
    }
    assert store.insert_article(payload) is True
    assert store.count() == 1
    assert store.insert_article(payload) is False
    assert store.count() == 1
    recent = store.list_recent(limit=5)
    assert recent[0].title == "Hello"
    store.close()
