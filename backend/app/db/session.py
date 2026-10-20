"""Async SQLAlchemy engine and session factory with automatic SQLite dev fallback."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

settings = get_settings()

# Resolve database URL
db_url = settings.DATABASE_URL

# Automatically normalize postgresql:// or postgres:// to postgresql+asyncpg:// for async engine
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

# If pointing to docker service 'db' but running locally without docker, fallback to SQLite
if "@db:5432" in db_url:
    db_url = "sqlite+aiosqlite:///muhurta.db"

if "sqlite" in db_url:
    engine = create_async_engine(
        db_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_async_engine(
        db_url,
        echo=(settings.ENV == "dev"),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
