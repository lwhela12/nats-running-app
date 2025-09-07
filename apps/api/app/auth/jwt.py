from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import jwt

from ..config import get_settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_token(sub: str, ttl_seconds: int, token_type: str) -> str:
    settings = get_settings()
    payload: Dict[str, Any] = {
        "sub": sub,
        "type": token_type,
        "iat": int(_now().timestamp()),
        "exp": int((_now() + timedelta(seconds=ttl_seconds)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])

