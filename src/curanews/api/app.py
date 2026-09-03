"""FastAPI application factory (Issue #16 / G16; UI mount G18)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from curanews import __version__
from curanews.api.routers import (
    articles,
    auth,
    bookmarks,
    comments,
    editor,
    feed,
    health,
    reads,
    seo,
    topics,
)
from curanews.config import get_settings

WEB_DIR = Path(__file__).resolve().parents[3] / "web"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="CuraNews Aggregator REST API — Phase 4 (G16+).",
    )
    app.include_router(health.router)
    app.include_router(seo.router)
    app.include_router(auth.router)
    app.include_router(bookmarks.router)
    app.include_router(comments.router)
    app.include_router(editor.router)
    app.include_router(articles.router)
    app.include_router(feed.router)
    app.include_router(reads.router)
    app.include_router(topics.router)

    if WEB_DIR.is_dir():
        app.mount("/ui", StaticFiles(directory=str(WEB_DIR), html=True), name="ui")

        @app.get("/", include_in_schema=False)
        def root_redirect() -> RedirectResponse:
            return RedirectResponse(url="/ui/")

        @app.get("/ui", include_in_schema=False)
        def ui_index() -> FileResponse:
            return FileResponse(WEB_DIR / "index.html")

    return app


app = create_app()
