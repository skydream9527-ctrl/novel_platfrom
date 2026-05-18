"""JWT (access + refresh) and password hashing."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

import bcrypt
from jose import JWTError, jwt

from .config import get_settings
from .errors import APIError, ErrorCode

JWT_ALG = "HS256"
_BCRYPT_MAX_BYTES = 72


def _truncate(plain: str) -> bytes:
    return plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_truncate(plain), bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(_truncate(plain), hashed.encode("ascii"))
    except (ValueError, TypeError):
        return False


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_access_token(user_id: str, role: str) -> str:
    s = get_settings()
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": int(_now().timestamp()),
        "exp": int((_now() + timedelta(minutes=s.ICE_ACCESS_TOKEN_TTL_MIN)).timestamp()),
    }
    return jwt.encode(payload, s.ICE_SECRET_KEY, algorithm=JWT_ALG)


def create_refresh_token(user_id: str) -> str:
    s = get_settings()
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": int(_now().timestamp()),
        "exp": int((_now() + timedelta(days=s.ICE_REFRESH_TOKEN_TTL_DAYS)).timestamp()),
    }
    return jwt.encode(payload, s.ICE_SECRET_KEY, algorithm=JWT_ALG)


def decode_token(token: str, expect: Literal["access", "refresh"] = "access") -> dict:
    s = get_settings()
    try:
        payload = jwt.decode(token, s.ICE_SECRET_KEY, algorithms=[JWT_ALG])
    except JWTError as e:
        # python-jose raises ExpiredSignatureError as a subclass; differentiate by str
        if "expired" in str(e).lower():
            raise APIError(401, ErrorCode.TOKEN_EXPIRED, "token expired") from e
        raise APIError(401, ErrorCode.TOKEN_INVALID, "invalid token") from e
    if payload.get("type") != expect:
        raise APIError(401, ErrorCode.TOKEN_INVALID, f"expected {expect} token")
    return payload
