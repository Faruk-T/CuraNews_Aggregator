"""Refresh CuraNews with public RSS headlines.

Usage::

    docker compose up -d postgres redis
    poetry run alembic upgrade head
    poetry run python scripts/refresh_news.py              # RSS only (production)
    poetry run python scripts/refresh_news.py --with-demo  # + demo users A/B (local dev)
    poetry run python scripts/run_api.py
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from curanews.ingestion.refresh import main as refresh_main

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-demo",
        action="store_true",
        help="also seed demo users and English placeholder stories (local dev only)",
    )
    args = parser.parse_args(argv)
    code = refresh_main()
    if code != 0 or not args.with_demo:
        return code
    demo = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "seed_demo_users.py")],
        cwd=ROOT,
        check=False,
    )
    return int(demo.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
