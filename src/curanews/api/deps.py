"""FastAPI dependencies (DB session)."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from curanews.db.session import get_session_factory


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped SQLAlchemy session."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
