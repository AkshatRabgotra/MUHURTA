"""Telegram reminder service and background runner."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from app.config import get_settings
from app.db.models import AnalyticsEvent, CalendarEvent, Reminder, Slot, User
from app.db.session import async_session_factory

logger = structlog.get_logger(__name__)
settings = get_settings()


class TelegramBotClient:
    """Telegram Bot API client."""

    def __init__(self, bot_token: str) -> None:
        self.bot_token = bot_token

    async def send_message(self, chat_id: str, text: str) -> bool:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                return True
            logger.error("Telegram API error", status_code=resp.status_code, body=resp.text)
            return False


class FakeTelegramBotClient:
    """Fake client logging reminders in credential-free mode."""

    async def send_message(self, chat_id: str, text: str) -> bool:
        logger.info(
            "Fake Telegram Client: reminder sent (credential-free mode)",
            chat_id=chat_id,
            text=text[:120],
        )
        return True


def get_telegram_client() -> TelegramBotClient | FakeTelegramBotClient:
    """Return configured Telegram client or Fake client."""
    if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN == "REPLACE_ME":
        return FakeTelegramBotClient()
    return TelegramBotClient(settings.TELEGRAM_BOT_TOKEN)


async def send_telegram_reminder(reminder: Reminder, user: User, slot: Slot | None, db: AsyncSession) -> bool:
    """Compose and send a reminder notification."""
    client = get_telegram_client()
    chat_id = user.telegram_chat_id or "dev_chat_id"

    slot_info = ""
    if slot:
        slot_info = (
            f"<b>Auspicious Muhurta Slot (Rank #{slot.rank})</b>\n"
            f"Time: {slot.start_utc.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"Score: {slot.score}\n\n"
            f"<i>{slot.explanation_text or ''}</i>"
        )
    else:
        slot_info = "Your scheduled Muhurta event is starting in 60 minutes."

    message_text = (
        f"🔔 <b>Muhurta Planner Reminder</b>\n\n"
        f"Your auspicious event is scheduled to begin in 1 hour!\n\n"
        f"{slot_info}"
    )

    success = await client.send_message(chat_id, message_text)
    return success


async def run_due_reminders(
    session_factory: Any | None = None,
    session: AsyncSession | None = None,
) -> dict[str, int]:
    """Find and send all pending reminders where send_at_utc <= now.
    Uses FOR UPDATE SKIP LOCKED for safe concurrent worker execution.
    Retries up to 3 attempts.
    """
    if session is not None:
        return await _process_reminders(session)

    factory = session_factory or async_session_factory
    async with factory() as s:
        return await _process_reminders(s)


async def _process_reminders(session: AsyncSession) -> dict[str, int]:
    now_utc = datetime.now(timezone.utc)
    processed = 0
    sent = 0
    failed = 0

    # Query with row-level locking on Postgres
    stmt = select(Reminder).where(
        Reminder.status == "pending",
        Reminder.send_at_utc <= now_utc,
        Reminder.attempts < 3,
    )
    if session.bind and session.bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update(skip_locked=True)

    res = await session.execute(stmt)
    due_reminders = res.scalars().all()

    for rem in due_reminders:
        processed += 1
        rem.attempts += 1

        # Fetch user and calendar event / slot
        user_res = await session.execute(select(User).where(User.id == rem.user_id))
        user = user_res.scalar_one_or_none()

        cal_res = await session.execute(select(CalendarEvent).where(CalendarEvent.id == rem.calendar_event_id))
        cal = cal_res.scalar_one_or_none()
        slot = None
        if cal:
            slot_res = await session.execute(select(Slot).where(Slot.id == cal.slot_id))
            slot = slot_res.scalar_one_or_none()

        if not user:
            rem.status = "failed"
            rem.last_error = "User not found"
            failed += 1
            continue

        try:
            ok = await send_telegram_reminder(rem, user, slot, session)
            if ok:
                rem.status = "sent"
                rem.sent_at = datetime.now(timezone.utc)
                sent += 1

                # Record analytics event
                analytics_ev = AnalyticsEvent(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    name="reminder_sent",
                    props={"reminder_id": str(rem.id), "channel": rem.channel},
                )
                session.add(analytics_ev)
            else:
                if rem.attempts >= 3:
                    rem.status = "failed"
                rem.last_error = "Failed to deliver message via Telegram client"
                failed += 1
        except Exception as exc:
            if rem.attempts >= 3:
                rem.status = "failed"
            rem.last_error = str(exc)
            failed += 1
            logger.error("Error processing reminder", reminder_id=str(rem.id), error=str(exc))

    await session.commit()
    logger.info("run_due_reminders completed", processed=processed, sent=sent, failed=failed)
    return {"processed": processed, "sent": sent, "failed": failed}
