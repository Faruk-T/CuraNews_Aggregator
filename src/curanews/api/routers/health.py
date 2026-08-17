"""GET /health — liveness + dependency probes (Issue #16)."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import create_engine, text

from curanews import __version__
from curanews.api.schemas import HealthResponse
from curanews.cache.redis_client import RedisClient
from curanews.config import get_settings

router = APIRouter(tags=["health"])


def _probe_database(database_url: str) -> bool:
    try:
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=1,
            max_overflow=0,
            connect_args={"connect_timeout": 1},
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:  # noqa: BLE001
        return False


def _probe_redis(redis_url: str) -> bool:
    try:
        return RedisClient(redis_url, socket_connect_timeout=0.25).ping()
    except Exception:  # noqa: BLE001
        return False


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    db_up = _probe_database(settings.database_url)
    redis_up = _probe_redis(settings.redis_url)
    return HealthResponse(
        status="ok" if db_up else "degraded",
        app=settings.app_name,
        version=__version__,
        database="up" if db_up else "down",
        redis="up" if redis_up else "down",
    )
