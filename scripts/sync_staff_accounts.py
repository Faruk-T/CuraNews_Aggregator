"""Provision the editor from EDITOR_EMAIL / EDITOR_PASSWORD and revoke leaked demo passwords.

In production (APP_ENV=prod) the example.com placeholder stories written by
``seed_demo_users.py`` are removed as well.

Usage::

    poetry run python scripts/sync_staff_accounts.py
"""

from __future__ import annotations

import logging

from curanews.api.accounts import purge_demo_articles, sync_staff_accounts
from curanews.config import get_settings
from curanews.db.session import get_session_factory


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    session = get_session_factory()()
    try:
        sync_staff_accounts(session)
        if get_settings().is_prod:
            purge_demo_articles(session)
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
