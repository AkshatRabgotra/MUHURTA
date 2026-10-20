"""Security utilities: Fernet encryption for OAuth tokens and JWT handling."""

from __future__ import annotations

import base64
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import Fernet
from jose import JWTError, jwt

from app.config import get_settings
from app.core.errors import AppError, ErrorCode

settings = get_settings()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def _get_fernet() -> Fernet:
    """Return a Fernet cipher instance using settings.FERNET_KEY.
    If the key is REPLACE_ME or invalid length, fallback to a deterministic dev key.
    """
    key = settings.FERNET_KEY
    if not key or key == "REPLACE_ME" or len(key) != 44:
        # 32-byte url-safe base64 key for dev fallback
        dev_key = base64.urlsafe_b64encode(b"01234567890123456789012345678901")
        return Fernet(dev_key)
    try:
        return Fernet(key.encode("utf-8"))
    except Exception:
        dev_key = base64.urlsafe_b64encode(b"01234567890123456789012345678901")
        return Fernet(dev_key)


def encrypt_token(plain_token: str) -> str:
    """Encrypt sensitive OAuth token before storing in DB."""
    if not plain_token:
        return ""
    f = _get_fernet()
    return f.encrypt(plain_token.encode("utf-8")).decode("utf-8")


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt sensitive OAuth token retrieved from DB."""
    if not encrypted_token:
        return ""
    f = _get_fernet()
    try:
        return f.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
    except Exception as exc:
        raise AppError(
            code=ErrorCode.INTERNAL,
            message="Failed to decrypt token.",
        ) from exc


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT token containing claims."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    secret = settings.JWT_SECRET if settings.JWT_SECRET != "REPLACE_ME" else "dev_jwt_secret_for_local_testing_only"
    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a signed JWT token."""
    secret = settings.JWT_SECRET if settings.JWT_SECRET != "REPLACE_ME" else "dev_jwt_secret_for_local_testing_only"
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        return payload
    except JWTError as exc:
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid or expired authentication credentials.",
            status_code=401,
        ) from exc


def hash_password(password: str) -> str:
    """Hash password using salt + sha256."""
    import hashlib
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()
    return f"{salt}${hashed}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored salt$hash."""
    import hashlib
    if not hashed_password or "$" not in hashed_password:
        return False
    salt, expected_hash = hashed_password.split("$", 1)
    actual_hash = hashlib.sha256(f"{salt}{plain_password}".encode("utf-8")).hexdigest()
    return actual_hash == expected_hash

