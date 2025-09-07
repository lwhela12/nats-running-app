from __future__ import annotations

from passlib.hash import argon2
from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr
from sqlalchemy.orm import Session

from ..auth.jwt import create_token
from ..config import get_settings
from ..db import get_db
from ..models import User
from ..schemas import RegisterRequest, TokenPair


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=str(payload.email),
        password_hash=argon2.hash(payload.password),
        age=payload.age,
        sex=payload.sex,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    settings = get_settings()
    at = create_token(user.id, settings.access_token_ttl, "access")
    rt = create_token(user.id, settings.refresh_token_ttl, "refresh")
    return TokenPair(access_token=at, refresh_token=rt)


class LoginRequest(RegisterRequest):
    email: EmailStr
    password: str
    age: int | None = None
    sex: str | None = None


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(payload.email)).first()
    if not user or not argon2.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    settings = get_settings()
    at = create_token(user.id, settings.access_token_ttl, "access")
    rt = create_token(user.id, settings.refresh_token_ttl, "refresh")
    return TokenPair(access_token=at, refresh_token=rt)


@router.post("/refresh", response_model=TokenPair)
def refresh(token: str, db: Session = Depends(get_db)):
    # For MVP: accept refresh token in body; issue new access+refresh
    from ..auth.jwt import decode_token

    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Not a refresh token")
    user = db.get(User, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    settings = get_settings()
    at = create_token(user.id, settings.access_token_ttl, "access")
    rt = create_token(user.id, settings.refresh_token_ttl, "refresh")
    return TokenPair(access_token=at, refresh_token=rt)

