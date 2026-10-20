"""SQLAlchemy declarative base with a UUID primary-key mixin."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB, UUID as PG_UUID, UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# ── SQLite Compatibility for Postgres Types ─────────────────────────────────
@compiles(PG_UUID, "sqlite")
def compile_pg_uuid_for_sqlite(type_, compiler, **kw):  # noqa: ANN001, ANN201
    return "TEXT"


@compiles(PG_JSONB, "sqlite")
def compile_pg_jsonb_for_sqlite(type_, compiler, **kw):  # noqa: ANN001, ANN201
    return "JSON"


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


class UUIDMixin:
    """Mixin that provides a UUID primary key and audit timestamps.

    Apply to any model via multiple inheritance::

        class User(UUIDMixin, Base):
            __tablename__ = "users"
            ...
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
