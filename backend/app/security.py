"""Password hashing, opaque-token hashing, and signed access-token helpers."""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.config import settings

password_hasher = PasswordHash.recommended()  # Argon2id: deliberately slow, salted password hashing.


def _jwt_secret() -> str:
    # Refuse to mint or accept tokens with a missing or weak signing key.
    key = settings.JWT_SECRET_KEY
    if not key or len(key) < 32:
        raise RuntimeError("Set JWT_SECRET_KEY to a random secret with at least 32 characters")
    return key


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        return password_hasher.verify(password, stored_hash)
    except Exception:
        return False


def new_secret() -> str:
    return secrets.token_urlsafe(48)  # High-entropy opaque value for refresh/email/reset links.


def digest_secret(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_access_token(user_id: uuid.UUID) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
    jti = str(uuid.uuid4())
    token = jwt.encode(
        {"sub": str(user_id), "jti": jti, "iat": now, "exp": expires,
         "iss": settings.JWT_ISSUER, "type": "access"},
        _jwt_secret(),
        algorithm="HS256",
    )
    return token, jti, expires


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token, _jwt_secret(), algorithms=["HS256"],
        issuer=settings.JWT_ISSUER, options={"require": ["sub", "jti", "exp", "iat"]},
    )
