"""Re-score stored article categories with the current classifier (idempotent).

Usage::

    poetry run python scripts/recategorize_articles.py
"""

from __future__ import annotations

import logging

from curanews.api.services import recategorize_articles
from curanews.db.session import get_session_factory


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    session = get_session_factory()()
    try:
        updated = recategorize_articles(session)
    finally:
        session.close()
    logging.info("recategorized %s articles", updated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
