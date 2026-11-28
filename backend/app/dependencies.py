"""Request dependencies, including installing the JWT identity into PostgreSQL."""
import uuid
from collections.abc import Generator

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.auth_token import AuthToken
from app.security import decode_access_token

bearer = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> uuid.UUID:
    unauthorized = HTTPException(status_code=401, detail="Invalid or expired access token")
    if credentials is None:
        raise unauthorized
    try:
        claims = decode_access_token(credentials.credentials)
        if claims.get("type") != "access":
            raise unauthorized
        user_id = uuid.UUID(claims["sub"])
        # Transaction-local identity lets existing PostgreSQL RLS policies scope queries.
        db.execute(text("SELECT set_config('app.current_user_id', :user_id, true)"), {"user_id": str(user_id)})
        revoked = db.scalar(select(AuthToken.id).where(
            AuthToken.user_id == user_id,
            AuthToken.purpose == "access_revoked",
            AuthToken.token_hash == claims["jti"],
        ))
        if revoked:
            raise unauthorized
        return user_id
    except (jwt.PyJWTError, ValueError, KeyError):
        raise unauthorized
