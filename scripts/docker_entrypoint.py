"""Docker entrypoint: wait for Postgres, migrate, optional bootstrap, serve API.

Usage (inside container)::

    python scripts/docker_entrypoint.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]


def wait_for_database(url: str, *, timeout_seconds: float = 60.0) -> None:
    deadline = time.time() + timeout_seconds
    last: Exception | None = None
    while time.time() < deadline:
        try:
            engine = create_engine(url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            print("database ready", flush=True)
            return
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.5)
    raise SystemExit(f"database not ready: {last}")


def main() -> int:
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://curanews:curanews@postgres:5432/curanews",
    )
    print("CuraNews entrypoint: waiting for database…", flush=True)
    wait_for_database(database_url)

    print("Running alembic upgrade head…", flush=True)
    subprocess.run(["alembic", "upgrade", "head"], cwd=ROOT, check=True)

    if os.environ.get("CURANEWS_BOOTSTRAP", "0") == "1":
        print("Bootstrapping sources + RSS + demo users…", flush=True)
        subprocess.run([sys.executable, str(ROOT / "scripts" / "seed_sources.py")], cwd=ROOT, check=False)
        subprocess.run([sys.executable, str(ROOT / "scripts" / "refresh_news.py")], cwd=ROOT, check=False)

    print("Starting uvicorn on 0.0.0.0:8000…", flush=True)
    os.execvp(
        "uvicorn",
        ["uvicorn", "curanews.api.app:app", "--host", "0.0.0.0", "--port", "8000"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
