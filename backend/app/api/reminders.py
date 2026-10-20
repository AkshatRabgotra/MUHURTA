"""Telegram linking, webhooks, and internal reminder runner endpoints."""

from __future__ import annotations

import secrets
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.api.auth import get_current_user
from app.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.db.models import User
from app.db.session import get_db
from app.schemas.common import RunRemindersResponse, TelegramLinkResponse, TelegramWebhookUpdate
from app.services.reminder_service import run_due_reminders

logger = structlog.get_logger(__name__)
settings = get_settings()
router = APIRouter(tags=["reminders"])


@router.post("/internal/run-reminders", response_model=RunRemindersResponse)
async def trigger_run_due_reminders(
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> RunRemindersResponse:
    """Protected endpoint to trigger processing of due reminders (called by cron / EventBridge)."""
    key = x_internal_key
    if not key and authorization and authorization.startswith("Bearer "):
        key = authorization[7:].strip()

    expected = settings.INTERNAL_API_KEY
    if expected != "REPLACE_ME" and key != expected:
        raise AppError(code=ErrorCode.UNAUTHORIZED, message="Invalid internal API key.", status_code=401)

    stats = await run_due_reminders(session=db)
    return RunRemindersResponse(
        processed=stats["processed"],
        sent=stats["sent"],
        failed=stats["failed"],
    )


@router.post("/me/telegram/link", response_model=TelegramLinkResponse)
async def generate_telegram_link(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TelegramLinkResponse:
    """Generate a one-time 6-character code and Telegram bot deep link."""
    code = secrets.token_hex(3).upper()  # 6-char hex
    current_user.telegram_link_code = code
    await db.commit()

    bot_name = settings.TELEGRAM_BOT_USERNAME if settings.TELEGRAM_BOT_USERNAME != "REPLACE_ME" else "MuhurtaPlannerBot"
    deep_link = f"https://t.me/{bot_name}?start={code}"

    return TelegramLinkResponse(code=code, deep_link=deep_link)


@router.post("/telegram/webhook")
async def telegram_webhook(
    update: TelegramWebhookUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Handle incoming Telegram webhook to link chat_id when user sends /start <code>."""
    msg = update.message or {}
    text = (msg.get("text") or "").strip()
    chat = msg.get("chat") or {}
    chat_id = str(chat.get("id"))

    if not chat_id:
        return {"ok": True}

    # Format: "/start <code>" or just "<code>"
    parts = text.split()
    code = parts[1].upper() if len(parts) > 1 and parts[0] == "/start" else parts[0].upper() if parts else ""

    if code:
        q = select(User).where(User.telegram_link_code == code)
        res = await db.execute(q)
        user = res.scalar_one_or_none()
        if user:
            user.telegram_chat_id = chat_id
            user.telegram_link_code = None  # consume single-use code
            await db.commit()
            logger.info("Linked user telegram chat_id", user_id=str(user.id), chat_id=chat_id)

    return {"ok": True}
