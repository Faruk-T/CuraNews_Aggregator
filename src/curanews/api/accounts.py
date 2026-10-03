"""Staff account provisioning driven by environment settings."""

from __future__ import annotations

import logging

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from curanews.api.auth import hash_password, verify_password
from curanews.config import Settings, get_settings
from curanews.db.models import (
    Article,
    ArticleEntity,
    Comment,
    Source,
    User,
    UserBookmark,
    UserRead,
)

logger = logging.getLogger(__name__)

EDITOR_KEY = "demo-editor"
READER_KEY = "demo-okur"
MIN_STAFF_PASSWORD_LENGTH = 12
DEMO_SOURCE_NAME = "example_news"
DEMO_URL_PREFIX = "https://example.com/"

# Published in early commits of this repository; never accept them again.
LEAKED_PASSWORDS: frozenset[str] = frozenset({"editor123", "faruk123", "okur123"})


def _uses_leaked_password(user: User) -> bool:
    if not user.hashed_password:
        return False
    return any(verify_password(pw, user.hashed_password) for pw in LEAKED_PASSWORDS)


def sync_staff_accounts(session: Session, settings: Settings | None = None) -> None:
    """Create/refresh the editor account and revoke credentials that leaked in git history."""
    cfg = settings or get_settings()
    email = cfg.editor_email.strip().lower()
    password = cfg.editor_password

    editor = (
        session.query(User)
        .filter((User.external_key == EDITOR_KEY) | (User.email == email))
        .first()
    )
    if editor is None:
        editor = User(
            external_key=EDITOR_KEY,
            email=email,
            full_name="Faruk Tazeoğlu",
            bio="CuraNews kurucusu ve baş editörü.",
            role="editor",
            preferences={"categories": ["gundem", "ekonomi", "teknoloji"]},
        )
        session.add(editor)
    editor.role = "editor"
    editor.email = email

    if password and len(password) >= MIN_STAFF_PASSWORD_LENGTH:
        if not editor.hashed_password or not verify_password(password, editor.hashed_password):
            editor.hashed_password = hash_password(password)
            logger.info("editor password updated for %s", email)
    else:
        if password:
            logger.warning(
                "EDITOR_PASSWORD shorter than %s chars ignored", MIN_STAFF_PASSWORD_LENGTH
            )
        if _uses_leaked_password(editor):
            editor.hashed_password = None
            logger.warning("editor login disabled: set EDITOR_PASSWORD to enable it")

    for user in session.query(User).filter(User.external_key != EDITOR_KEY).all():
        if _uses_leaked_password(user):
            user.hashed_password = None
            logger.warning("revoked leaked demo password for %s", user.external_key)

    session.commit()


def purge_demo_articles(session: Session) -> int:
    """Delete the English placeholder stories that dev seeding writes under example.com."""
    ids = list(
        session.scalars(
            select(Article.id)
            .join(Source, Source.id == Article.source_id)
            .where(Source.name == DEMO_SOURCE_NAME)
            .where(Article.url.startswith(DEMO_URL_PREFIX))
        )
    )
    if not ids:
        return 0
    for model in (ArticleEntity, UserRead, UserBookmark, Comment):
        session.execute(delete(model).where(model.article_id.in_(ids)))
    session.execute(delete(Article).where(Article.id.in_(ids)))
    session.commit()
    logger.info("purged %s demo articles", len(ids))
    return len(ids)
