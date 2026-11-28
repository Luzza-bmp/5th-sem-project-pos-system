"""Account registration and authentication endpoints."""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import get_current_user_id, get_db
from app.models.auth_session import AuthSession
from app.models.auth_token import AuthToken
from app.models.user import User
from app.schemas.auth import (EmailRequest, LoginRequest, RefreshRequest,
                              RegisterRequest, ResetPasswordRequest, TokenPair,
                              UserResponse)
from app.security import (create_access_token, digest_secret, hash_password,
                          new_secret, verify_password)
from app.services.email import send_auth_link

router = APIRouter(prefix="/auth", tags=["authentication"])


def issue_pair(db: Session, user_id: uuid.UUID, session: AuthSession | None = None) -> TokenPair:
    access, jti, access_expiry = create_access_token(user_id)
    refresh = new_secret()
    refresh_expiry = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_DAYS)
    if session is None:
        session = AuthSession(user_id=user_id, refresh_token_hash=digest_secret(refresh),
                              access_jti=jti, expires_at=refresh_expiry)
        db.add(session)
    else:
        session.refresh_token_hash = digest_secret(refresh)  # Rotate: old refresh secret stops working.
        session.access_jti = jti
        session.expires_at = refresh_expiry
    db.commit()
    return TokenPair(access_token=access, refresh_token=refresh,
                     expires_in=settings.ACCESS_TOKEN_MINUTES * 60)


def create_one_time_token(db: Session, user_id: uuid.UUID, purpose: str,
                          lifetime: timedelta) -> str:
    raw = new_secret()
    db.add(AuthToken(user_id=user_id, purpose=purpose, token_hash=digest_secret(raw),
                     expires_at=datetime.now(timezone.utc) + lifetime))
    db.commit()
    return raw


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Create only a user account. Store creation is a separate authenticated action."""
    email = str(payload.email).strip().lower()
    password_hash = hash_password(payload.password)
    try:
        user_id = db.execute(text("SELECT public.auth_register_user(:email, :password_hash)"),
                              {"email": email, "password_hash": password_hash}).scalar_one()
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    return {"message": "Account created. You can now sign in and create a store.",
            "user_id": str(user_id)}


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    # This narrow SECURITY DEFINER lookup allows login by email while the users
    # table itself remains protected by its own-user RLS policy.
    user_data = db.execute(text("SELECT * FROM public.auth_user_by_email(:email)"), {"email": email}).first()
    # Same response for unknown email and wrong password avoids account discovery.
    if not user_data or not verify_password(payload.password, user_data.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    return issue_pair(db, user_data.id)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    row = db.scalar(select(AuthSession).where(
        AuthSession.refresh_token_hash == digest_secret(payload.refresh_token),
        AuthSession.revoked_at.is_(None),
        AuthSession.expires_at > datetime.now(timezone.utc),
    ).with_for_update())
    if not row:
        raise HTTPException(status_code=401, detail="Refresh token is invalid or expired")
    # Rotation also invalidates the access token paired with the old refresh token.
    db.add(AuthToken(user_id=row.user_id, purpose="access_revoked",
                     token_hash=row.access_jti,
                     expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)))
    return issue_pair(db, row.user_id, row)


@router.post("/logout")
def logout(payload: RefreshRequest, user_id: uuid.UUID = Depends(get_current_user_id),
           db: Session = Depends(get_db)):
    row = db.scalar(select(AuthSession).where(
        AuthSession.user_id == user_id,
        AuthSession.refresh_token_hash == digest_secret(payload.refresh_token),
        AuthSession.revoked_at.is_(None),
    ).with_for_update())
    if row:
        now = datetime.now(timezone.utc)
        row.revoked_at = now
        db.add(AuthToken(user_id=user_id, purpose="access_revoked",
                         token_hash=row.access_jti,
                         expires_at=now + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)))
        db.commit()
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
def me(user_id: uuid.UUID = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(id=str(user.id), email=user.email)


@router.post("/password-reset/request")
def request_password_reset(payload: EmailRequest, db: Session = Depends(get_db)):
    """Always returns the same message so callers cannot enumerate accounts."""
    email = str(payload.email).strip().lower()
    user_data = db.execute(text("SELECT * FROM public.auth_user_by_email(:email)"), {"email": email}).first()
    if user_data:
        raw = create_one_time_token(db, user_data.id, "password_reset", timedelta(minutes=30))
        send_auth_link(email, "reset-password", raw)
    return {"message": "If that account exists, a password reset link has been sent."}


@router.post("/password-reset/confirm")
def confirm_password_reset(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    row = db.scalar(select(AuthToken).where(
        AuthToken.purpose == "password_reset",
        AuthToken.token_hash == digest_secret(payload.token),
        AuthToken.used_at.is_(None), AuthToken.expires_at > now,
    ).with_for_update())
    if not row:
        raise HTTPException(status_code=400, detail="Reset link is invalid or expired")
    db.execute(text("SELECT set_config('app.current_user_id', :uid, true)"), {"uid": str(row.user_id)})
    user = db.get(User, row.user_id)
    user.password_hash = hash_password(payload.new_password)
    row.used_at = now
    # Password change signs out every device, including already-issued access tokens.
    active_sessions = db.scalars(select(AuthSession).where(
        AuthSession.user_id == row.user_id, AuthSession.revoked_at.is_(None)
    )).all()
    for session in active_sessions:
        session.revoked_at = now
        db.add(AuthToken(user_id=row.user_id, purpose="access_revoked",
                         token_hash=session.access_jti,
                         expires_at=now + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)))
    db.commit()
    return {"message": "Password updated. Sign in again on your devices."}
