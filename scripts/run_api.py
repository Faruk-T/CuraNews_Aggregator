"""Run the CuraNews FastAPI server (Issue #16 / G16).

Usage::

    poetry run python scripts/run_api.py
    # then open http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import uvicorn

from curanews.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "curanews.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_dev,
    )


if __name__ == "__main__":
    main()
