"""Unit tests for Auth and Password/JWT helpers (Day 22)."""

from __future__ import annotations

from uuid import uuid4

from curanews.api.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing_and_verification() -> None:
    secret = "GucluSifre2026!"
    hashed = hash_password(secret)

    assert hashed.startswith("pbkdf2:sha256:100000$")
    assert verify_password(secret, hashed) is True
    assert verify_password("YanlisSifre", hashed) is False
    assert verify_password("", hashed) is False


def test_jwt_token_lifecycle() -> None:
    uid = uuid4()
    key = "test-user-123"
    token = create_access_token(uid, key, role="editor", expires_in_seconds=3600)

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == str(uid)
    assert payload["key"] == key
    assert payload["role"] == "editor"


def test_jwt_expired_token() -> None:
    uid = uuid4()
    # Expired 10 seconds ago
    token = create_access_token(uid, "expired-user", role="reader", expires_in_seconds=-10)
    payload = decode_access_token(token)
    assert payload is None


def test_jwt_tampered_token() -> None:
    uid = uuid4()
    token = create_access_token(uid, "user", role="reader")
    parts = token.split(".")
    tampered = f"{parts[0]}.{parts[1]}wrong.{parts[2]}"
    assert decode_access_token(tampered) is None
