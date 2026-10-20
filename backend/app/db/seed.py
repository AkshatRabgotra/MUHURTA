"""Seed script for local development and testing."""

from __future__ import annotations

import asyncio
import uuid
import structlog
from sqlalchemy import select

from app.db.models import User
from app.db.session import async_session_factory

logger = structlog.get_logger(__name__)

DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000099")
DEV_USER_EMAIL = "dev@muhurta.local"


async def seed_dev_user(session: AsyncSession | None = None) -> User:
    """Ensure a deterministic test user exists in the database for dev/testing."""
    if session is not None:
        return await _ensure_user(session)
    async with async_session_factory() as s:
        return await _ensure_user(s)


async def _ensure_user(session: AsyncSession) -> User:
    result = await session.execute(
        select(User).where((User.id == DEV_USER_ID) | (User.email == DEV_USER_EMAIL))
    )
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            id=DEV_USER_ID,
            email=DEV_USER_EMAIL,
            name="Test Dev User",
            google_sub="dev_google_sub_0001",
            timezone="Asia/Kolkata",
            default_city="Bengaluru, India",
            telegram_chat_id="12345678",
            telegram_link_code="DEV123",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("Created seed dev user", user_id=str(user.id), email=user.email)
    return user


if __name__ == "__main__":
    asyncio.run(seed_dev_user())
