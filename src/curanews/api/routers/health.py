"""GET /health — liveness + dependency probes (Issue #16)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import create_engine, text

from curanews import __version__
from curanews.api.schemas import HealthResponse
from curanews.cache.redis_client import RedisClient
from curanews.config import get_settings
from curanews.ingestion.scheduler import scheduler_interval_seconds
from curanews.ingestion.status import read_ingest_status

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


def _as_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    db_up = _probe_database(settings.database_url)
    redis_up = _probe_redis(settings.redis_url)
    ingest = read_ingest_status()
    interval = int(scheduler_interval_seconds(settings) // 60)
    inserted = ingest.get("inserted")
    return HealthResponse(
        status="ok" if db_up else "degraded",
        app=settings.app_name,
        version=__version__,
        database="up" if db_up else "down",
        redis="up" if redis_up else "down",
        ingest_interval_minutes=interval,
        last_ingest_at=_as_datetime(ingest.get("finished_at") or ingest.get("started_at")),
        last_ingest_inserted=inserted if isinstance(inserted, int) else None,
        last_ingest_status=ingest.get("status") if isinstance(ingest.get("status"), str) else None,
    )
