"""FastAPI application factory (Issue #16 / G16; UI mount G18)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
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
    pages,
    reads,
    seo,
    topics,
)
from curanews.api.urls import base_path
from curanews.config import get_settings
from curanews.ingestion.scheduler import IngestScheduler
from curanews.web.render import WEB_DIR

CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self' https://www.googletagmanager.com",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data: https:",
        "connect-src 'self' https://*.google-analytics.com https://*.analytics.google.com "
        "https://www.googletagmanager.com",
        "frame-src https://www.youtube-nocookie.com https://player.vimeo.com",
        "frame-ancestors 'self'",
        "base-uri 'self'",
        "form-action 'self'",
        "object-src 'none'",
    ]
)
_DOCS_PREFIXES = ("/docs", "/redoc", "/openapi.json")


def _install_security_headers(app: FastAPI, *, hsts: bool) -> None:
    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        headers = response.headers
        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if hsts:
            headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        if not request.url.path.startswith(_DOCS_PREFIXES):
            headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        if request.url.path.startswith(("/auth/", "/feed", "/bookmarks", "/reads")):
            headers.setdefault("Cache-Control", "no-store")
        return response


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        scheduler = IngestScheduler.from_settings(settings)
        scheduler.start()
        try:
            yield
        finally:
            scheduler.stop()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="CuraNews Aggregator REST API — Phase 4 (G16+).",
        docs_url=None if settings.is_prod else "/docs",
        redoc_url=None if settings.is_prod else "/redoc",
        lifespan=lifespan,
    )
    _install_security_headers(app, hsts=settings.is_prod)

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

        @app.get("/", include_in_schema=False)
        def root_redirect(request: Request) -> RedirectResponse:
            return RedirectResponse(url=f"{base_path(request)}/ui/", status_code=301)

        @app.get("/ui", include_in_schema=False)
        def ui_slash_redirect() -> RedirectResponse:
            return RedirectResponse(url="ui/", status_code=301)

        app.include_router(pages.router)
        app.mount("/ui", StaticFiles(directory=str(WEB_DIR)), name="ui")

    return app


app = create_app()
