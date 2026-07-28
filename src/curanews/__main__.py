"""CLI entrypoint: ``python -m curanews`` / ``curanews``."""

from __future__ import annotations

import logging

from curanews import __version__
from curanews.config import get_settings
from curanews.logging_setup import setup_logging

logger = logging.getLogger("curanews")


def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level, app_name="curanews")
    logger.info(
        "startup app=%s version=%s env=%s",
        settings.app_name,
        __version__,
        settings.app_env,
    )
    print(f"{settings.app_name} — ready (day 2)")
    print(f"package: curanews v{__version__}")
    print(f"env: {settings.app_env} | log_level: {settings.log_level}")


if __name__ == "__main__":
    main()
