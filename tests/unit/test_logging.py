"""Smoke tests for logging setup."""

import logging

from curanews.logging_setup import setup_logging


def test_setup_logging_sets_level():
    root = logging.getLogger()
    # Clear handlers so setup runs fully in this process.
    for handler in list(root.handlers):
        root.removeHandler(handler)

    setup_logging("WARNING", app_name="curanews")
    assert root.level == logging.WARNING
    assert root.handlers
