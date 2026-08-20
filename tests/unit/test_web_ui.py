"""Web UI mount tests (Issue #18 / G18)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from curanews.api.app import create_app


def test_ui_index_is_served() -> None:
    client = TestClient(create_app())
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "CuraNews" in response.text
    assert "feedList" in response.text


def test_root_redirects_to_ui() -> None:
    client = TestClient(create_app())
    response = client.get("/", follow_redirects=False)
    assert response.status_code in {307, 302}
    assert response.headers["location"].endswith("/ui/")


def test_ui_assets_are_served() -> None:
    client = TestClient(create_app())
    css = client.get("/ui/styles.css")
    js = client.get("/ui/app.js")
    assert css.status_code == 200
    assert "Fraunces" in css.text or "--brand" in css.text or "--accent" in css.text
    assert js.status_code == 200
    assert "loadFeed" in js.text
