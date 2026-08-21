"""Run the full regression suite (Issue #19 / G19).

Usage:
  poetry run python scripts/run_tests.py
  poetry run python scripts/run_tests.py -m unit
  poetry run python scripts/run_tests.py -m integration
  poetry run python scripts/run_tests.py tests/integration -v
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    cmd = [sys.executable, "-m", "pytest", *args]
    print("+", " ".join(cmd), flush=True)
    completed = subprocess.run(cmd, cwd=ROOT)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
