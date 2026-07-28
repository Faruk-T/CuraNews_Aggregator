"""Structured logging configuration."""

from __future__ import annotations

import logging
import sys
from typing import Literal


LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def setup_logging(level: LogLevel = "INFO", *, app_name: str = "curanews") -> None:
    """Configure root logging once for CLI and API entrypoints.

    Uses a compact key=value style that is easy to grep in internship demos.
    """
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s level=%(levelname)s logger=%(name)s msg=%(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(level)

    logging.getLogger(app_name).debug("logging configured level=%s", level)
