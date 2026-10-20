"""SQLAlchemy ORM models for the Muhurta Planner.

All tables use UUID primary keys, created_at/updated_at timestamps,
and proper foreign keys with indexes.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# ── Users ────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_sub: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, default="Asia/Kolkata"
    )
    default_city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    telegram_link_code: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # relationships
    google_token: Mapped[GoogleToken | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    plan_requests: Mapped[list[PlanRequest]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


# ── Google Tokens (encrypted at rest) ────────────────────────────────────
class GoogleToken(Base):
    __tablename__ = "google_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    access_token_enc: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_enc: Mapped[str] = mapped_column(Text, nullable=False)
    expiry: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scopes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="google_token")


# ── Plan Requests ────────────────────────────────────────────────────────
class PlanRequest(Base):
    __tablename__ = "plan_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_constraints: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="general")
    override: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    basis: Mapped[str] = mapped_column(String(32), nullable=False, default="category")
    runner_up_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    advisory_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    shortage_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    clarification: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prompt_variant: Mapped[str | None] = mapped_column(String(32), nullable=True)
    llm_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    llm_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # relationships
    user: Mapped[User] = relationship(back_populates="plan_requests")
    slots: Mapped[list[Slot]] = relationship(
        back_populates="plan_request", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_plan_requests_user_id", "user_id"),
        Index("ix_plan_requests_created_at", "created_at"),
    )


# ── Slots ────────────────────────────────────────────────────────────────
class Slot(Base):
    __tablename__ = "slots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plan_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reasons: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    explanation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    rank: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    plan_request: Mapped[PlanRequest] = relationship(back_populates="slots")
    calendar_event: Mapped[CalendarEvent | None] = relationship(
        back_populates="slot", uselist=False, cascade="all, delete-orphan"
    )
    feedback: Mapped[list[Feedback]] = relationship(
        back_populates="slot", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_slots_plan_request_id", "plan_request_id"),
    )


# ── Calendar Events ─────────────────────────────────────────────────────
class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("slots.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    google_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    slot: Mapped[Slot] = relationship(back_populates="calendar_event")
    reminders: Mapped[list[Reminder]] = relationship(
        back_populates="calendar_event", cascade="all, delete-orphan"
    )


# ── Reminders ────────────────────────────────────────────────────────────
class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    calendar_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calendar_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    send_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    channel: Mapped[str] = mapped_column(
        String(32), nullable=False, default="telegram"
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending"
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    calendar_event: Mapped[CalendarEvent] = relationship(back_populates="reminders")

    __table_args__ = (
        Index("ix_reminders_send_at_status", "send_at_utc", "status"),
    )


# ── Feedback ─────────────────────────────────────────────────────────────
class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("slots.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    slot: Mapped[Slot] = relationship(back_populates="feedback")

    __table_args__ = (
        Index("ix_feedback_slot_id", "slot_id"),
    )


# ── Analytics Events ────────────────────────────────────────────────────
class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    plan_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plan_requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    props: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_analytics_events_name", "name"),
        Index("ix_analytics_events_user_id", "user_id"),
    )
