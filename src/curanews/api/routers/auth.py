"""Authentication and user profile router (Day 22)."""

from __future__ import annotations

import re
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from curanews.api.auth import (
    create_access_token,
    get_current_user_required,
    hash_password,
    verify_password,
)
from curanews.api.deps import get_db
from curanews.api.ratelimit import client_ip, enforce, login_limiter, register_limiter
from curanews.api.schemas import AuthResponse, UserLogin, UserProfile, UserRegister
from curanews.api.urls import safe_http_url
from curanews.db.models import User, UserBookmark, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

EMAIL_PATTERN = re.compile(r"[^@\s]{1,64}@[^@\s]{1,190}\.[a-z]{2,24}")


def _user_to_profile(session: Session, user: User) -> UserProfile:
    reads_stmt = select(UserRead).where(UserRead.user_id == user.id)
    bms_stmt = select(UserBookmark).where(UserBookmark.user_id == user.id)
    read_count = len(list(session.scalars(reads_stmt).all()))
    bookmarks_count = len(list(session.scalars(bms_stmt).all()))
    return UserProfile(
        id=user.id,
        external_key=user.external_key,
        email=user.email,
        full_name=user.full_name or user.external_key,
        avatar_url=user.avatar_url,
        bio=user.bio,
        role=user.role,
        preferences=user.preferences or {},
        read_count=read_count,
        bookmarks_count=bookmarks_count,
    )


@router.post("/register", response_model=AuthResponse)
def register(
    req: UserRegister, request: Request, session: Session = Depends(get_db)
) -> AuthResponse:
    enforce(register_limiter, client_ip(request))
    email = req.email.lower().strip()
    if not EMAIL_PATTERN.fullmatch(email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Geçerli bir e-posta adresi girin.",
        )
    existing = session.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi ile zaten bir hesap mevcut.",
        )

    user = User(
        external_key=f"user-{uuid.uuid4().hex[:12]}",
        email=email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name.strip(),
        role="reader",
        preferences=req.preferences,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_access_token(user.id, user.external_key, role=user.role)
    return AuthResponse(access_token=token, user=_user_to_profile(session, user))


@router.post("/login", response_model=AuthResponse)
def login(req: UserLogin, request: Request, session: Session = Depends(get_db)) -> AuthResponse:
    email = req.email.lower().strip()
    enforce(login_limiter, f"{client_ip(request)}|{email}")
    user = session.query(User).filter(User.email == email).first()

    valid_pw = bool(
        user and user.hashed_password and verify_password(req.password, user.hashed_password)
    )
    if not valid_pw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı.",
        )

    token = create_access_token(user.id, user.external_key, role=user.role)
    return AuthResponse(access_token=token, user=_user_to_profile(session, user))


@router.get("/me", response_model=UserProfile)
def get_current_profile(
    current_user: User = Depends(get_current_user_required),
    session: Session = Depends(get_db),
) -> UserProfile:
    return _user_to_profile(session, current_user)


@router.put("/me", response_model=UserProfile)
def update_profile(
    req: dict[str, Any],
    current_user: User = Depends(get_current_user_required),
    session: Session = Depends(get_db),
) -> UserProfile:
    if "full_name" in req and req["full_name"]:
        current_user.full_name = str(req["full_name"]).strip()[:120]
    if "avatar_url" in req:
        current_user.avatar_url = safe_http_url(req["avatar_url"])
    if "bio" in req:
        current_user.bio = str(req["bio"]).strip()[:500] if req["bio"] else None
    if "preferences" in req and isinstance(req["preferences"], dict):
        current_user.preferences = req["preferences"]

    session.commit()
    session.refresh(current_user)
    return _user_to_profile(session, current_user)
