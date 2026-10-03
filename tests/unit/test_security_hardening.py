"""Account security, URL sanitising, timestamp correction and categorisation regressions."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from tests.support.db import seed_article, seed_source, sqlite_session_fixture

from curanews.api.accounts import purge_demo_articles, sync_staff_accounts
from curanews.api.app import create_app
from curanews.api.auth import hash_password, verify_password
from curanews.api.deps import get_db
from curanews.api.urls import safe_http_url, slugify, video_embed_url
from curanews.config import Settings
from curanews.db.models import Article, User, UserRead
from curanews.ingestion.cleaning import strip_html_tags
from curanews.nlp.categorizer import categorize_text
from curanews.scrapers.adapters.rss import parse_feed_xml
from curanews.scrapers.adapters.rss_catalog import RssFeed
from curanews.timeutil import correct_future_timestamp


@pytest.fixture
def session() -> Generator[Session, None, None]:
    yield from sqlite_session_fixture()


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    app = create_app()

    def _db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = _db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------- auth endpoints


def test_register_always_creates_reader(client: TestClient, session: Session) -> None:
    res = client.post(
        "/auth/register",
        json={
            "email": "Yeni@Example.com",
            "password": "uzun-bir-sifre",
            "full_name": "Yeni Okur",
            "role": "editor",
        },
    )
    assert res.status_code == 200
    profile = res.json()["user"]
    assert profile["role"] == "reader"
    assert profile["external_key"].startswith("user-")
    user = session.query(User).filter(User.email == "yeni@example.com").one()
    assert user.role == "reader"


def test_register_rejects_invalid_email(client: TestClient) -> None:
    res = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "uzun-bir-sifre", "full_name": "X Y"},
    )
    assert res.status_code == 422


@pytest.mark.parametrize("password", ["editor123", "faruk123", "okur123"])
def test_leaked_demo_passwords_no_longer_log_in(
    client: TestClient, session: Session, password: str
) -> None:
    session.add(User(external_key="demo-editor", email="faruk@curanews.com", role="editor"))
    session.commit()
    res = client.post("/auth/login", json={"email": "faruk@curanews.com", "password": password})
    assert res.status_code == 401


def test_login_rate_limit(client: TestClient) -> None:
    payload = {"email": "kimse@example.com", "password": "yanlis-sifre"}
    codes = [client.post("/auth/login", json=payload).status_code for _ in range(11)]
    assert codes[:10] == [401] * 10
    assert codes[-1] == 429


# ------------------------------------------------------------ staff provisioning


def _settings(**overrides: str) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[call-arg]


def test_sync_staff_accounts_sets_strong_editor_password(session: Session) -> None:
    sync_staff_accounts(
        session, _settings(editor_email="ed@example.com", editor_password="a-strong-secret-42")
    )
    editor = session.query(User).filter(User.external_key == "demo-editor").one()
    assert editor.role == "editor"
    assert editor.email == "ed@example.com"
    assert verify_password("a-strong-secret-42", editor.hashed_password or "")


def test_sync_staff_accounts_revokes_leaked_passwords(session: Session) -> None:
    session.add_all(
        [
            User(
                external_key="demo-editor",
                email="faruk@curanews.com",
                role="editor",
                hashed_password=hash_password("editor123"),
            ),
            User(
                external_key="demo-okur",
                email="okur@curanews.com",
                hashed_password=hash_password("okur123"),
            ),
            User(
                external_key="user-keepme0001",
                email="real@example.com",
                hashed_password=hash_password("kendi-sifresi"),
            ),
        ]
    )
    session.commit()

    sync_staff_accounts(session, _settings(editor_password="short"))

    by_key = {u.external_key: u for u in session.query(User).all()}
    assert by_key["demo-editor"].hashed_password is None
    assert by_key["demo-okur"].hashed_password is None
    assert verify_password("kendi-sifresi", by_key["user-keepme0001"].hashed_password or "")


def test_purge_demo_articles_keeps_real_news(session: Session) -> None:
    demo_source = seed_source(session, name="example_news")
    real_source = seed_source(session, name="bbc_turkce")
    demo = seed_article(
        session,
        demo_source,
        title="Markets rally on rate-cut hopes",
        url_path="news/curation-economy-demo",
        url_hash="d" * 64,
        category="economy",
        topics=["economy"],
    )
    real = seed_article(
        session,
        real_source,
        title="Gerçek haber",
        url_path="real",
        url_hash="r" * 64,
        category="gundem",
        topics=["gundem"],
    )
    real.url = "https://www.bbc.com/turkce/real"
    reader = User(external_key="demo-user-a")
    session.add(reader)
    session.flush()
    session.add(UserRead(user_id=reader.id, article_id=demo.id, dwell_ms=1000))
    session.commit()

    assert purge_demo_articles(session) == 1
    assert purge_demo_articles(session) == 0
    remaining = {a.title for a in session.query(Article).all()}
    assert remaining == {"Gerçek haber"}
    assert session.query(UserRead).count() == 0


# -------------------------------------------------------------------- URL helpers


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
        ),
        ("https://youtu.be/dQw4w9WgXcQ", "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"),
        (
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
        ),
        ("https://vimeo.com/123456789", "https://player.vimeo.com/video/123456789"),
        ("javascript:alert(1)", None),
        ("https://evil.example.com/embed/dQw4w9WgXcQ", None),
        ('https://www.youtube.com/watch?v=bad"id', None),
        ("", None),
    ],
)
def test_video_embed_url(raw: str, expected: str | None) -> None:
    assert video_embed_url(raw) == expected


@pytest.mark.parametrize(
    ("raw", "ok"),
    [
        ("https://example.com/a.jpg", True),
        ("http://example.com/a.jpg", True),
        ("javascript:alert(1)", False),
        ("data:image/svg+xml;base64,AAAA", False),
        ("//example.com/a.jpg", False),
        ("https://" + "a" * 3000, False),
    ],
)
def test_safe_http_url(raw: str, ok: bool) -> None:
    assert (safe_http_url(raw) is not None) is ok


def test_slugify_turkish() -> None:
    assert slugify("İsrail'de Çığ Gibi Büyüyen Öfke: Şok Açıklama!") == (
        "israil-de-cig-gibi-buyuyen-ofke-sok-aciklama"
    )
    assert slugify("???") == "haber"


# ------------------------------------------------------------- content quality


def test_future_timestamp_from_mislabelled_feed_is_shifted() -> None:
    now = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
    istanbul_as_gmt = now + timedelta(hours=2, minutes=50)
    assert correct_future_timestamp(istanbul_as_gmt, now=now) == istanbul_as_gmt - timedelta(
        hours=3
    )


def test_far_future_timestamp_is_clamped_to_now() -> None:
    now = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
    assert correct_future_timestamp(now + timedelta(days=2), now=now) == now


def test_past_timestamp_is_unchanged() -> None:
    now = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)
    past = now - timedelta(hours=5)
    assert correct_future_timestamp(past, now=now) == past
    assert correct_future_timestamp(None, now=now) is None


def test_free_form_item_tag_keeps_feed_desk() -> None:
    feed = RssFeed(
        key="aljazeera_english",
        publisher="Al Jazeera",
        url="https://www.aljazeera.com/xml/rss/all.xml",
        category="world",
        language="en",
        host="www.aljazeera.com",
    )
    xml = """<rss version="2.0"><channel><item>
        <title>Defining consent after a campus case</title>
        <link>https://www.aljazeera.com/news/1</link>
        <description>How a student went from blaming herself to reporting.</description>
        <category>News</category>
    </item></channel></rss>"""
    [draft] = parse_feed_xml(xml, feed=feed)
    assert draft.category == "dunya"
    assert draft.metadata["feed_category"] == "world"


@pytest.mark.parametrize(
    ("title", "summary", "feed_category", "expected"),
    [
        ("İsrail Başbakanı Netanyahu'dan Gazze açıklaması", "", "gundem", "dunya"),
        (
            "Kanser tedavisinde yeni ilaç hastanelerde kullanılmaya başlandı",
            "Hastalar için umut",
            "teknoloji",
            "saglik",
        ),
        ("Derbide Galatasaray Fenerbahçe'yi 2-1 yendi", "", "gundem", "spor"),
        ("EuroLeague'de haftanın MVP'si belli oldu", "", "sports", "spor"),
        ("Israeli settlers attack farmers in West Bank", "", "world", "dunya"),
        ("Ebola bilançosu: Can kaybı 4 bini geçti", "", "turkey", "saglik"),
        ("Merkez Bankası faiz kararını açıkladı", "Enflasyon ve büyüme", "gundem", "ekonomi"),
    ],
)
def test_categorizer_turkish_dotted_i(
    title: str, summary: str, feed_category: str, expected: str
) -> None:
    slug, _ = categorize_text(title, summary=summary, default_category=feed_category)
    assert slug == expected


def test_html_entities_are_decoded_once() -> None:
    assert strip_html_tags("<p>Erdoğan&#039;dan &quot;yeni&quot; açıklama</p>") == (
        'Erdoğan\'dan "yeni" açıklama'
    )
