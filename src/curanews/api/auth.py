"""Authentication, password hashing, and JWT token management (Day 22).

Uses standard PBKDF2-HMAC-SHA256 for cryptographic password hashing and
RFC 7519 compliant HMAC-SHA256 JWT tokens.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from curanews.api.deps import get_db
from curanews.config import get_settings
from curanews.db.models import User

_bearer_security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a random salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"pbkdf2:sha256:100000${salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed: str) -> bool:
    """Verify a plain password against the stored PBKDF2 hash."""
    if not hashed or not hashed.startswith("pbkdf2:sha256:"):
        return False
    try:
        parts = hashed.split("$")
        if len(parts) != 3:
            return False
        iterations = int(parts[0].split(":")[2])
        salt = bytes.fromhex(parts[1])
        expected_key = bytes.fromhex(parts[2])
        computed_key = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt, iterations
        )
        return hmac.compare_digest(expected_key, computed_key)
    except Exception:
        return False


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_access_token(
    user_id: UUID | str,
    external_key: str,
    role: str = "reader",
    expires_in_seconds: int = 86400 * 7,  # 7 days
) -> str:
    """Create signed HS256 JWT access token."""
    settings = get_settings()
    secret = (settings.pii_hash_salt or "curanews-secret-key-2026").encode("utf-8")

    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "key": external_key,
        "role": role,
        "iat": now,
        "exp": now + expires_in_seconds,
    }

    header_b64 = _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode()

    signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
    sig_b64 = _b64encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Verify and decode signed JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        settings = get_settings()
        secret = (settings.pii_hash_salt or "curanews-secret-key-2026").encode("utf-8")
        signing_input = f"{header_b64}.{payload_b64}".encode()

        expected_sig = hmac.new(secret, signing_input, hashlib.sha256).digest()
        actual_sig = _b64decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload_bytes = _b64decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        if payload.get("exp", 0) < int(time.time()):
            return None

        return payload
    except Exception:
        return None


def get_current_user_optional(
    auth: HTTPAuthorizationCredentials | None = Depends(_bearer_security),
    session: Session = Depends(get_db),
) -> User | None:
    """Extract authenticated user if bearer token is provided; otherwise None."""
    if not auth or not auth.credentials:
        return None

    payload = decode_access_token(auth.credentials)
    if not payload or not payload.get("key"):
        return None

    user = session.query(User).filter(User.external_key == payload["key"]).first()
    return user


def get_current_user_required(
    current_user: User | None = Depends(get_current_user_optional),
) -> User:
    """Ensure user is logged in; raises 401 Unauthorized if not."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bu işlem için giriş yapmanız gerekmektedir.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user
