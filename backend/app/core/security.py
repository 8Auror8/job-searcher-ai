"""Password hashing, opaque tokens and JWT access tokens."""

import hashlib
import secrets
import uuid
from datetime import timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import Settings
from app.core.db import utcnow

_hasher = PasswordHasher()  # argon2id with library defaults
_DUMMY_HASH = _hasher.hash("timing-attack-dummy-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def dummy_password_check() -> None:
    """Spend the same time as a real check so response timing doesn't reveal unknown emails."""
    verify_password("not-the-password", _DUMMY_HASH)


def generate_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    """Opaque tokens are stored hashed; a DB leak doesn't expose usable tokens."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: uuid.UUID, settings: Settings) -> str:
    now = utcnow()
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> uuid.UUID | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "type"]},
        )
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "access":
        return None
    try:
        return uuid.UUID(payload["sub"])
    except (ValueError, TypeError):
        return None


def sign_state(data: dict[str, str], settings: Settings, minutes: int = 10) -> str:
    """Short-lived signed blob (used for the Google OAuth state/PKCE cookie)."""
    payload: dict[str, object] = {
        **data,
        "type": "oauth_state",
        "exp": utcnow() + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def read_state(token: str, settings: Settings) -> dict[str, str] | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "oauth_state":
        return None
    return {k: str(v) for k, v in payload.items() if k not in {"type", "exp"}}
