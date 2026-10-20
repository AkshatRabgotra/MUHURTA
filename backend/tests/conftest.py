"""Pytest configuration and fixtures with SQLite in-memory test database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.core.security import create_access_token
from app.db.base import Base
from app.db.models import User
from app.db.session import get_db
from app.main import app

# ── SQLite Compatibility for Postgres Types ─────────────────────────────────
@compiles(PG_UUID, "sqlite")
def compile_pg_uuid_for_sqlite(type_, compiler, **kw):  # noqa: ANN001, ANN201
    return "TEXT"


@compiles(PG_JSONB, "sqlite")
def compile_pg_jsonb_for_sqlite(type_, compiler, **kw):  # noqa: ANN001, ANN201
    return "JSON"


# In-memory test engine
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
TestSessionFactory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionFactory() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_test_db() -> AsyncGenerator[None, None]:
    """Create all tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed test user
    async with TestSessionFactory() as session:
        user = User(
            id=TEST_USER_ID,
            email="testuser@example.com",
            name="Test User",
            timezone="Asia/Kolkata",
            default_city="Bengaluru, India",
            telegram_chat_id="987654321",
        )
        session.add(user)
        await session.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Yield an unauthenticated async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture()
async def auth_client() -> AsyncGenerator[AsyncClient, None]:
    """Yield an authenticated async test client with session cookie and auth header."""
    token = create_access_token({"sub": str(TEST_USER_ID), "email": "testuser@example.com"})
    transport = ASGITransport(app=app)
    cookies = {"access_token": token}
    headers = {"Authorization": f"Bearer {token}"}
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies, headers=headers) as ac:
        yield ac
