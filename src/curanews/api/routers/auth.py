"""Authentication and user profile router (Day 22)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from curanews.api.auth import (
    create_access_token,
    get_current_user_required,
    hash_password,
    verify_password,
)
from curanews.api.deps import get_db
from curanews.api.schemas import AuthResponse, UserLogin, UserProfile, UserRegister
from curanews.db.models import User, UserBookmark, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


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
def register(req: UserRegister, session: Session = Depends(get_db)) -> AuthResponse:
    existing = session.query(User).filter(User.email == req.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi ile zaten bir hesap mevcut.",
        )

    external_key = f"user-{uuid.uuid4().hex[:8]}"
    user = User(
        external_key=external_key,
        email=req.email.lower().strip(),
        hashed_password=hash_password(req.password),
        full_name=req.full_name.strip(),
        avatar_url=req.avatar_url,
        role=req.role,
        preferences=req.preferences,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_access_token(user.id, user.external_key, role=user.role)
    return AuthResponse(access_token=token, user=_user_to_profile(session, user))


@router.post("/login", response_model=AuthResponse)
def login(req: UserLogin, session: Session = Depends(get_db)) -> AuthResponse:
    email_clean = req.email.lower().strip()
    ensure_demo_accounts(session)

    if email_clean in ("faruk@curanews.com", "editor@curanews.com"):
        user = session.query(User).filter(
            (User.email == "faruk@curanews.com")
            | (User.email == "editor@curanews.com")
            | (User.external_key == "demo-editor")
        ).first()
    else:
        user = session.query(User).filter(User.email == email_clean).first()

    valid_pw = False
    if user:
        if user.external_key == "demo-editor" and req.password in ("editor123", "faruk123"):
            valid_pw = True
        elif user.hashed_password:
            valid_pw = verify_password(req.password, user.hashed_password)

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
        current_user.full_name = str(req["full_name"]).strip()
    if "avatar_url" in req:
        current_user.avatar_url = str(req["avatar_url"]).strip() if req["avatar_url"] else None
    if "bio" in req:
        current_user.bio = str(req["bio"]).strip() if req["bio"] else None
    if "preferences" in req and isinstance(req["preferences"], dict):
        current_user.preferences = req["preferences"]

    session.commit()
    session.refresh(current_user)
    return _user_to_profile(session, current_user)


def ensure_demo_accounts(session: Session) -> None:
    """Pre-seed standard demo accounts for company presentation and faculty defense."""
    demo_editor = session.query(User).filter(
        (User.external_key == "demo-editor")
        | (User.email == "editor@curanews.com")
        | (User.email == "faruk@curanews.com")
    ).first()
    if not demo_editor:
        demo_editor = User(
            external_key="demo-editor",
            email="faruk@curanews.com",
            hashed_password=hash_password("editor123"),
            full_name="Faruk Tazeoğlu (Baş Editör & Kurucu)",
            avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
            bio="CuraNews Kurucusu, Baş Editör ve Sistem Mimarı.",
            role="editor",
            preferences={"categories": ["gundem", "ekonomi", "teknoloji"]},
        )
        session.add(demo_editor)
    else:
        demo_editor.full_name = "Faruk Tazeoğlu (Baş Editör & Kurucu)"
        demo_editor.bio = "CuraNews Kurucusu, Baş Editör ve Sistem Mimarı."
        demo_editor.role = "editor"
        if not demo_editor.email:
            demo_editor.email = "faruk@curanews.com"

    demo_reader = session.query(User).filter(User.email == "okur@curanews.com").first()
    if not demo_reader:
        demo_reader = User(
            external_key="demo-okur",
            email="okur@curanews.com",
            hashed_password=hash_password("okur123"),
            full_name="Mehmet Özkan (Kamu Görevlisi)",
            avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
            bio="Gündem ve ekonomi haberlerini düzenli takip eden kıdemli memur.",
            role="reader",
            preferences={"categories": ["gundem", "ekonomi"]},
        )
        session.add(demo_reader)

    session.commit()
