"""Authentication routes: Google OAuth, Dev Login, and User Profile."""

from __future__ import annotations

import secrets
import urllib.parse
import uuid
from typing import Any

from fastapi import APIRouter, Cookie, Depends, Header, Response
from fastapi.responses import RedirectResponse
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.core.security import (
    create_access_token,
    decode_access_token,
    encrypt_token,
    hash_password,
    verify_password,
)
from app.db.models import GoogleToken, User
from app.db.seed import DEV_USER_EMAIL, DEV_USER_ID, seed_dev_user
from app.db.session import get_db
from app.schemas.common import UserLoginRequest, UserRead, UserRegisterRequest, UserUpdate

logger = structlog.get_logger(__name__)
settings = get_settings()
router = APIRouter(tags=["auth"])

COOKIE_NAME = "access_token"


# ── Dependency: Get Current User ─────────────────────────────────────────────

async def get_optional_current_user(
    db: AsyncSession = Depends(get_db),
    access_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    authorization: str | None = Header(default=None),
) -> User | None:
    """Extract authenticated user if token is present and valid; returns None for guests without raising."""
    token = access_token
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()

    if not token:
        return None

    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if not sub:
            return None
        user_id = uuid.UUID(sub)
        q = select(User).where(User.id == user_id)
        res = await db.execute(q)
        return res.scalar_one_or_none()
    except Exception:
        return None


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    access_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    authorization: str | None = Header(default=None),
) -> User:
    """Extract authenticated user from httpOnly cookie or Authorization Bearer header.
    Raises 401 if unauthenticated.
    """
    token = access_token
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()

    if not token:
        raise AppError(code=ErrorCode.UNAUTHORIZED, message="Authentication required.", status_code=401)

    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if not sub:
            raise AppError(code=ErrorCode.UNAUTHORIZED, message="Invalid token payload.", status_code=401)
        user_id = uuid.UUID(sub)
    except Exception as exc:
        raise AppError(code=ErrorCode.UNAUTHORIZED, message="Invalid or expired token.", status_code=401) from exc

    q = select(User).where(User.id == user_id)
    res = await db.execute(q)
    user = res.scalar_one_or_none()
    if not user:
        raise AppError(code=ErrorCode.UNAUTHORIZED, message="User not found.", status_code=401)

    return user


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/auth/google/login")
async def google_login() -> RedirectResponse:
    """Redirect to Google OAuth consent screen."""
    if not settings.GOOGLE_CLIENT_ID or settings.GOOGLE_CLIENT_ID == "REPLACE_ME":
        raise AppError(
            code=ErrorCode.BAD_REQUEST,
            message="Google OAuth credentials are not configured in environment.",
        )

    # Standard non-sensitive scopes (allows instant Google login without requiring restricted app verification)
    scopes = [
        "openid",
        "email",
        "profile",
    ]
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
        "state": secrets.token_urlsafe(16),
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=url)


@router.get("/auth/google/callback")
async def google_callback(
    code: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Exchange authorization code, upsert user, store encrypted tokens, and set session cookie."""
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_resp = await client.post(token_url, data=token_data)
        if token_resp.status_code != 200:
            raise AppError(
                code=ErrorCode.BAD_REQUEST,
                message=f"Google token exchange failed: {token_resp.text}",
            )
        tokens = token_resp.json()
        access_token = tokens["access_token"]
        refresh_token = tokens.get("refresh_token", "")

        # Fetch user info
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            raise AppError(code=ErrorCode.BAD_REQUEST, message="Failed to fetch Google profile.")
        profile = userinfo_resp.json()

    google_sub = profile.get("sub")
    email = profile.get("email")
    name = profile.get("name", "")

    # Upsert user
    q = select(User).where((User.google_sub == google_sub) | (User.email == email))
    res = await db.execute(q)
    user = res.scalar_one_or_none()

    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            name=name,
            google_sub=google_sub,
            timezone="Asia/Kolkata",
        )
        db.add(user)
        await db.flush()
    else:
        user.google_sub = google_sub
        if name and not user.name:
            user.name = name

    # Store encrypted tokens
    token_q = select(GoogleToken).where(GoogleToken.user_id == user.id)
    token_res = await db.execute(token_q)
    gt = token_res.scalar_one_or_none()
    if not gt:
        gt = GoogleToken(
            user_id=user.id,
            access_token_enc=encrypt_token(access_token),
            refresh_token_enc=encrypt_token(refresh_token),
            scopes=tokens.get("scope", ""),
        )
        db.add(gt)
    else:
        gt.access_token_enc = encrypt_token(access_token)
        if refresh_token:
            gt.refresh_token_enc = encrypt_token(refresh_token)
        gt.scopes = tokens.get("scope", "")

    await db.commit()

    # Issue JWT session cookie
    jwt_token = create_access_token({"sub": str(user.id), "email": user.email})
    redirect_target = f"{settings.FRONTEND_URL}/planner?token={jwt_token}"
    resp = RedirectResponse(url=redirect_target, status_code=303)
    resp.set_cookie(
        key=COOKIE_NAME,
        value=jwt_token,
        httponly=True,
        samesite="none" if settings.ENV != "dev" else "lax",
        secure=(settings.ENV != "dev"),
    )
    return resp


@router.post("/auth/register")
async def register_user(
    payload: UserRegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Register a new user with email and password."""
    email = payload.email.lower().strip()
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise AppError(code=ErrorCode.BAD_REQUEST, message="An account with this email already exists.", status_code=400)

    user = User(
        email=email,
        name=payload.name or email.split("@")[0],
        password_hash=hash_password(payload.password),
        timezone=payload.timezone or "Asia/Kolkata",
        default_city=payload.default_city,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    jwt_token = create_access_token({"sub": str(user.id), "email": user.email})
    response.set_cookie(
        key=COOKIE_NAME,
        value=jwt_token,
        httponly=True,
        samesite="lax",
        secure=(settings.ENV != "dev"),
    )
    return {
        "message": "User registered successfully",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "timezone": user.timezone,
            "default_city": user.default_city,
        },
        "token": jwt_token,
    }


@router.post("/auth/login")
async def login_user(
    payload: UserLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Authenticate user with email and password."""
    email = payload.email.lower().strip()
    q = select(User).where(User.email == email)
    res = await db.execute(q)
    user = res.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise AppError(code=ErrorCode.UNAUTHORIZED, message="Invalid email or password.", status_code=401)

    jwt_token = create_access_token({"sub": str(user.id), "email": user.email})
    response.set_cookie(
        key=COOKIE_NAME,
        value=jwt_token,
        httponly=True,
        samesite="lax",
        secure=(settings.ENV != "dev"),
    )
    return {
        "message": "Logged in successfully",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "timezone": user.timezone,
            "default_city": user.default_city,
        },
        "token": jwt_token,
    }


@router.post("/auth/logout")
async def logout_user(response: Response) -> dict[str, str]:
    """Clear access token cookie."""
    response.delete_cookie(key=COOKIE_NAME)
    return {"message": "Logged out successfully"}


@router.post("/auth/dev-login")
async def dev_login(response: Response, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Logs in as seeded dev user (ONLY available when ENV=dev)."""
    if settings.ENV != "dev":
        raise AppError(code=ErrorCode.FORBIDDEN, message="Dev login is disabled in this environment.", status_code=403)

    user = await seed_dev_user(db)
    jwt_token = create_access_token({"sub": str(user.id), "email": user.email})

    response.set_cookie(
        key=COOKIE_NAME,
        value=jwt_token,
        httponly=True,
        samesite="lax",
        secure=False,
    )

    return {
        "message": "Logged in as test dev user",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "timezone": user.timezone,
        },
        "token": jwt_token,
    }


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    """Return authenticated user profile."""
    return UserRead(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        timezone=current_user.timezone,
        default_city=current_user.default_city,
        telegram_chat_id=current_user.telegram_chat_id,
    )


@router.patch("/me", response_model=UserRead)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Update timezone and default city."""
    if payload.timezone is not None:
        current_user.timezone = payload.timezone
    if payload.default_city is not None:
        current_user.default_city = payload.default_city

    await db.commit()
    await db.refresh(current_user)

    return UserRead(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        timezone=current_user.timezone,
        default_city=current_user.default_city,
        telegram_chat_id=current_user.telegram_chat_id,
    )
