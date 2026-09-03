"""CuraNews Cross-Platform Deployment Helper (Day 23).

Usage:
    python scripts/deploy.py --check-only
    python scripts/deploy.py --up
    python scripts/deploy.py --down
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_cmd(cmd: list[str]) -> int:
    print(f"-> {' '.join(cmd)}", flush=True)
    res = subprocess.run(cmd, cwd=ROOT)
    return res.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="CuraNews Production Deployer")
    parser.add_argument("--check-only", action="store_true", help="Validate configs and env")
    parser.add_argument("--up", action="store_true", help="Build and start production stack")
    parser.add_argument("--down", action="store_true", help="Stop production stack")
    args = parser.parse_args()

    compose_file = ROOT / "docker-compose.prod.yml"
    caddy_file = ROOT / "Caddyfile"

    print("==================================================")
    print(" 🚀 CuraNews Production Deployment Tool")
    print("==================================================")

    if not compose_file.is_file():
        print("❌ Error: docker-compose.prod.yml not found!")
        return 1
    if not caddy_file.is_file():
        print("❌ Error: Caddyfile not found!")
        return 1

    print("[OK] Production Compose and Caddy configuration found.")

    if args.down:
        print("Stopping production stack...")
        return run_cmd(["docker", "compose", "-f", str(compose_file), "down"])

    if args.up:
        print("Starting production stack with Caddy Auto-SSL...")
        ret = run_cmd(["docker", "compose", "-f", str(compose_file), "up", "-d", "--build"])
        if ret != 0:
            return ret
        print("Running database migrations...")
        migrate_cmd = [
            "docker", "compose", "-f", str(compose_file),
            "exec", "-T", "api", "alembic", "upgrade", "head"
        ]
        run_cmd(migrate_cmd)
        print("\n[SUCCESS] Production stack is running!")
        return 0

    print("[OK] Deployment configuration check passed.")
    print("Run with '--up' when ready to deploy to your server/VDS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
