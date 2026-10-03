"""Helpers for creating signed-in users in API tests."""

from __future__ import annotations

from sqlalchemy.orm import Session

from curanews.api.auth import create_access_token, hash_password
from curanews.db.models import User


def create_account(
    session: Session,
    *,
    key: str = "user-test0001",
    email: str = "okur@example.com",
    role: str = "reader",
    full_name: str = "Test Okur",
    password: str = "correct-horse-battery",
) -> User:
    user = User(
        external_key=key,
        email=email,
        role=role,
        full_name=full_name,
        hashed_password=hash_password(password),
    )
    session.add(user)
    session.commit()
    return user


def bearer(user: User) -> dict[str, str]:
    token = create_access_token(user.id, user.external_key, user.role)
    return {"Authorization": f"Bearer {token}"}
