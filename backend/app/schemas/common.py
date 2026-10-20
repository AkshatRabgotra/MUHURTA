"""Pydantic schemas for users, feedback, analytics, and integrations."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr, Field


# ── User Schemas ─────────────────────────────────────────────────────────
class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    timezone: str
    default_city: str | None = None
    telegram_chat_id: str | None = None


class UserUpdate(BaseModel):
    timezone: str | None = None
    default_city: str | None = None


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = ""
    timezone: str = "Asia/Kolkata"
    default_city: str | None = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str



# ── Feedback Schemas ─────────────────────────────────────────────────────
class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=-1, le=1)  # 1 or -1
    comment: str | None = Field(default=None, max_length=1000)


class FeedbackResponse(BaseModel):
    id: uuid.UUID
    slot_id: uuid.UUID
    user_id: uuid.UUID
    rating: int
    comment: str | None = None
    created_at: datetime


# ── Calendar Schemas ─────────────────────────────────────────────────────
class CalendarEventResponse(BaseModel):
    calendar_event_id: uuid.UUID
    google_event_id: str | None = None
    message: str


# ── Reminder Schemas ─────────────────────────────────────────────────────
class RunRemindersResponse(BaseModel):
    processed: int
    sent: int
    failed: int


# ── Telegram Schemas ─────────────────────────────────────────────────────
class TelegramLinkResponse(BaseModel):
    code: str
    deep_link: str


class TelegramWebhookUpdate(BaseModel):
    update_id: int | None = None
    message: dict[str, Any] | None = None


# ── Analytics Schemas ────────────────────────────────────────────────────
class FunnelVariantStats(BaseModel):
    prompt_variant: str
    request_created: int
    slots_viewed: int
    slot_added_to_calendar: int
    reminder_sent: int
    feedback_given: int
    conversion_rate_viewed_to_calendar: float = 0.0


class FunnelReportResponse(BaseModel):
    variants: list[FunnelVariantStats]
