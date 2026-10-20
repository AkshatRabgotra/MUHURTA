"""Google Calendar integration service with fake client fallback for credential-free development."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.core.security import decrypt_token, encrypt_token
from app.db.models import CalendarEvent, GoogleToken, Reminder, Slot, User

logger = structlog.get_logger(__name__)
settings = get_settings()


class GoogleCalendarClient:
    """Client for Google Calendar API with token refresh and error handling."""

    def __init__(self, access_token: str, refresh_token: str, user_id: uuid.UUID) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.user_id = user_id

    async def create_event(
        self,
        summary: str,
        description: str,
        start_utc: datetime,
        end_utc: datetime,
        user_tz: str,
        db: AsyncSession,
    ) -> str:
        """Create a Google Calendar event. Returns google_event_id."""
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        body = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start_utc.isoformat(),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_utc.isoformat(),
                "timeZone": "UTC",
            },
            "reminders": {
                "useDefault": False,
                "overrides": [{"method": "popup", "minutes": 60}],
            },
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=body)

            # If token expired (401), attempt refresh once
            if resp.status_code == 401:
                logger.info("Google access token expired, refreshing...", user_id=str(self.user_id))
                refreshed = await self._refresh_access_token(db)
                if not refreshed:
                    raise AppError(
                        code=ErrorCode.UNAUTHORIZED,
                        message="Google Calendar access was revoked or expired. Please reconnect your account.",
                        status_code=401,
                    )
                headers["Authorization"] = f"Bearer {self.access_token}"
                resp = await client.post(url, headers=headers, json=body)

            if resp.status_code not in (200, 201):
                logger.error("Google Calendar API call failed", status_code=resp.status_code, response=resp.text)
                raise AppError(
                    code=ErrorCode.SERVICE_UNAVAILABLE,
                    message=f"Failed to create Google Calendar event: {resp.text}",
                    status_code=502,
                )

            data = resp.json()
            return data.get("id", str(uuid.uuid4()))

    async def _refresh_access_token(self, db: AsyncSession) -> bool:
        """Exchange refresh_token for a new access_token."""
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(token_url, data=data)
                if resp.status_code == 200:
                    payload = resp.json()
                    new_access = payload.get("access_token")
                    if new_access:
                        self.access_token = new_access
                        # Update encrypted token in DB
                        q = select(GoogleToken).where(GoogleToken.user_id == self.user_id)
                        res = await db.execute(q)
                        gt = res.scalar_one_or_none()
                        if gt:
                            gt.access_token_enc = encrypt_token(new_access)
                            await db.flush()
                        return True
        except Exception as exc:
            logger.error("Failed to refresh Google token", error=str(exc))
        return False


class FakeGoogleCalendarClient:
    """Mock client for local dev without Google credentials."""

    def __init__(self, user_id: uuid.UUID) -> None:
        self.user_id = user_id

    async def create_event(
        self,
        summary: str,
        description: str,
        start_utc: datetime,
        end_utc: datetime,
        user_tz: str,
        db: AsyncSession,
    ) -> str:
        fake_event_id = f"mock_gcal_{uuid.uuid4().hex[:12]}"
        logger.info(
            "Fake Google Calendar: Event created (credential-free mode)",
            event_id=fake_event_id,
            summary=summary,
            start_utc=start_utc.isoformat(),
            end_utc=end_utc.isoformat(),
            user_id=str(self.user_id),
        )
        return fake_event_id


async def get_calendar_client(user_id: uuid.UUID, db: AsyncSession) -> GoogleCalendarClient | FakeGoogleCalendarClient:
    """Return configured Google Calendar client or Fake client if credentials missing."""
    if not settings.GOOGLE_CLIENT_ID or settings.GOOGLE_CLIENT_ID == "REPLACE_ME":
        return FakeGoogleCalendarClient(user_id)

    # Check if user has connected Google tokens
    res = await db.execute(select(GoogleToken).where(GoogleToken.user_id == user_id))
    gt = res.scalar_one_or_none()
    if not gt:
        # If credentials set but user hasn't authed with Google, use fake in dev
        if settings.ENV == "dev":
            return FakeGoogleCalendarClient(user_id)
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Google Calendar account not connected. Please connect via settings.",
            status_code=401,
        )

    access_tok = decrypt_token(gt.access_token_enc)
    refresh_tok = decrypt_token(gt.refresh_token_enc)
    return GoogleCalendarClient(access_tok, refresh_tok, user_id)


async def add_slot_to_calendar(
    slot_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> tuple[CalendarEvent, Reminder]:
    """Transaction requirement:
    In one single DB transaction, create the CalendarEvent row and the Reminder row.
    If the Google API call fails, nothing is committed.
    Use unique constraint plus idempotency so double-click cannot create two calendar events.
    """
    # 1. Check idempotency: if calendar event already exists for this slot, return it
    existing_q = select(CalendarEvent).where(CalendarEvent.slot_id == slot_id)
    res = await db.execute(existing_q)
    existing_event = res.scalar_one_or_none()
    if existing_event:
        # Fetch reminder
        rem_q = select(Reminder).where(Reminder.calendar_event_id == existing_event.id)
        rem_res = await db.execute(rem_q)
        existing_reminder = rem_res.scalar_one_or_none()
        return existing_event, existing_reminder  # type: ignore[return-value]

    # 2. Fetch slot with plan request and user
    slot_res = await db.execute(select(Slot).where(Slot.id == slot_id))
    slot = slot_res.scalar_one_or_none()
    if not slot:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Slot not found", status_code=404)

    user_res = await db.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()
    user_tz = user.timezone if user else "Asia/Kolkata"

    # 3. Call Google Calendar API (or fake client) BEFORE committing DB changes
    client = await get_calendar_client(user_id, db)
    summary = f"Muhurta: Auspicious Time Slot (Score {slot.score})"
    description = (
        f"Auspicious Muhurta Slot (Rank #{slot.rank})\n\n"
        f"Explanation:\n{slot.explanation_text or 'N/A'}\n\n"
        f"Scheduled via Muhurta Planner."
    )

    google_event_id = await client.create_event(
        summary=summary,
        description=description,
        start_utc=slot.start_utc,
        end_utc=slot.end_utc,
        user_tz=user_tz,
        db=db,
    )

    # 4. Atomic DB transaction: create CalendarEvent and Reminder
    cal_event = CalendarEvent(
        id=uuid.uuid4(),
        slot_id=slot.id,
        user_id=user_id,
        google_event_id=google_event_id,
    )
    db.add(cal_event)
    await db.flush()

    # Reminder 60 minutes before slot start
    send_at_utc = slot.start_utc - timedelta(minutes=60)
    reminder = Reminder(
        id=uuid.uuid4(),
        calendar_event_id=cal_event.id,
        user_id=user_id,
        send_at_utc=send_at_utc,
        channel="telegram",
        status="pending",
        attempts=0,
    )
    db.add(reminder)
    await db.commit()

    logger.info(
        "Slot added to calendar and reminder scheduled",
        slot_id=str(slot.id),
        calendar_event_id=str(cal_event.id),
        google_event_id=google_event_id,
    )

    return cal_event, reminder
