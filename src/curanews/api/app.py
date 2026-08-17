"""FastAPI application factory (Issue #16 / G16)."""

from __future__ import annotations

from fastapi import FastAPI

from curanews import __version__
from curanews.api.routers import articles, feed, health, reads, topics
from curanews.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="CuraNews Aggregator REST API — Phase 4 (G16+).",
    )
    app.include_router(health.router)
    app.include_router(articles.router)
    app.include_router(feed.router)
    app.include_router(reads.router)
    app.include_router(topics.router)
    return app


app = create_app()
