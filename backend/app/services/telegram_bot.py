"""Telegram Bot Polling Service.

Listens for incoming Telegram messages, handles /start, /link, greetings,
and directly processes natural language Muhurta calculation requests in Telegram.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
import json
import urllib.parse
import httpx
from sqlalchemy import select
import structlog

from app.config import get_settings
from app.db.models import User
from app.db.session import async_session_factory
from app.services.planner import create_plan

logger = structlog.get_logger(__name__)
settings = get_settings()

TELEGRAM_API_BASE = "https://api.telegram.org/bot"


async def send_telegram_message(
    chat_id: int | str,
    text: str,
    parse_mode: str = "Markdown",
    reply_markup: dict | None = None,
) -> bool:
    """Send a message to a Telegram chat using Bot API."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token or token == "REPLACE_ME":
        return False

    url = f"{TELEGRAM_API_BASE}{token}/sendMessage"
    payload: dict = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200 and resp.json().get("ok"):
                return True
            logger.warning("Failed to send Telegram message", status=resp.status_code, body=resp.text)
            # Retry without markdown if markdown parsing failed
            if "can't parse entities" in resp.text:
                payload["parse_mode"] = ""
                await client.post(url, json=payload)
                return True
    except Exception as exc:
        logger.error("Error sending Telegram message", error=str(exc))
    return False


async def send_chat_action(chat_id: int | str, action: str = "typing") -> None:
    """Send typing action to indicate the bot is computing."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token or token == "REPLACE_ME":
        return
    url = f"{TELEGRAM_API_BASE}{token}/sendChatAction"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, json={"chat_id": chat_id, "action": action})
    except Exception:
        pass


def _format_time_str(dt_str: str) -> str:
    """Format ISO datetime string nicely."""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%a, %b %d • %I:%M %p")
    except Exception:
        return dt_str


async def handle_update(update: dict) -> None:
    """Handle a single Telegram update."""
    message = update.get("message")
    if not message:
        return

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if not chat_id:
        return

    user_info = message.get("from") or {}
    first_name = user_info.get("first_name", "Friend")
    raw_text = (message.get("text") or "").strip()

    if not raw_text:
        return

    lower_text = raw_text.lower()

    # 1. Handle /start or /help
    if lower_text.startswith("/start") or lower_text in ("/help", "help", "hi", "hello", "namaste", "hey"):
        parts = raw_text.split()
        code = parts[1].strip().upper() if len(parts) > 1 and parts[0] == "/start" else ""

        # If a linking code was provided in /start <code>
        if code:
            async with async_session_factory() as db:
                q = select(User).where(User.telegram_link_code == code)
                res = await db.execute(q)
                user = res.scalar_one_or_none()
                if user:
                    user.telegram_chat_id = str(chat_id)
                    user.telegram_link_code = None
                    await db.commit()
                    await send_telegram_message(
                        chat_id,
                        f"✨ *Account Linked Successfully!* 🙏\n\n"
                        f"Namaste {first_name}! Your Telegram account is now connected to your Muhurta Planner profile ({user.email}).\n\n"
                        f"You will receive automatic alerts 1 hour before your scheduled auspicious windows.\n\n"
                        f"You can also ask me for auspicious timings anytime right here!",
                    )
                    return
                else:
                    await send_telegram_message(
                        chat_id,
                        "⚠️ That link code is invalid or has expired. Please generate a fresh code from your Web Dashboard.",
                    )
                    return

        # Regular /start or greeting
        welcome_text = (
            f"Namaste {first_name}! 🙏 Welcome to *Vedic Muhurta Planner* 🪔\n\n"
            f"I am your classical Vedic timing assistant, powered by the deterministic Swiss Ephemeris astronomical engine.\n\n"
            f"🌟 *Ask me directly for auspicious timings!*\n"
            f"Simply send your planned activity, for example:\n"
            f"• `Sign rental agreement this Friday morning in Bengaluru`\n"
            f"• `Buy a new car next week in Mumbai`\n"
            f"• `Griha Pravesh ceremony in Delhi next month`\n"
            f"• `Purchasing gold jewelry this weekend in Chennai`\n\n"
            f"🔗 *Link Your Web Profile:*\n"
            f"Send `/link <code>` using the code from your web dashboard to sync your consultations."
        )
        await send_telegram_message(chat_id, welcome_text)
        return

    # 2. Handle /link <code>
    if lower_text.startswith("/link"):
        parts = raw_text.split()
        if len(parts) < 2:
            await send_telegram_message(
                chat_id,
                "Please provide your 6-character link code from the web dashboard, like:\n`/link A1B2C3`",
            )
            return

        code = parts[1].strip().upper()
        async with async_session_factory() as db:
            q = select(User).where(User.telegram_link_code == code)
            res = await db.execute(q)
            user = res.scalar_one_or_none()
            if user:
                user.telegram_chat_id = str(chat_id)
                user.telegram_link_code = None
                await db.commit()
                await send_telegram_message(
                    chat_id,
                    f"✅ *Successfully Linked!* 🙏\n\n"
                    f"Your Telegram is now connected to *{user.email}*. All your consultations and 1-hour reminders will be synchronized.",
                )
            else:
                await send_telegram_message(
                    chat_id,
                    "⚠️ Invalid or expired code. Please generate a new code from the web app.",
                )
        return

    # 3. Natural Language Muhurta Query
    # Indicate typing while computing Swiss Ephemeris & Groq LLM
    await send_chat_action(chat_id, "typing")

    try:
        # Check if user is linked
        linked_user_id = None
        async with async_session_factory() as db:
            q = select(User).where(User.telegram_chat_id == str(chat_id))
            res = await db.execute(q)
            user = res.scalar_one_or_none()
            if user:
                linked_user_id = user.id

            # Run planner
            plan = await create_plan(
                user_id=linked_user_id,
                raw_text=raw_text,
                db=db,
            )

        if not plan.slots:
            clarify = plan.clarification or "Please provide the city name and preferred timeframe (e.g. *in Bengaluru this Friday morning*)."
            await send_telegram_message(
                chat_id,
                f"🪔 *Need a bit more information:*\n\n{clarify}",
            )
            return

        # Format Top 3 slots response
        city_display = plan.location_name or "Local Area"
        category_display = (plan.override or plan.category or "Auspicious Timing").replace("_", " ").title()

        msg_lines = [
            f"🪔 *Vedic Muhurta Recommendations*",
            f"🎯 *Activity:* {category_display}",
            f"📍 *Location:* {city_display}",
            f"━━━━━━━━━━━━━━━━━━━",
        ]

        for s in plan.slots[:3]:
            start_str = _format_time_str(str(s.start_utc))
            end_str = _format_time_str(str(s.end_utc))
            reasons_summary = ", ".join([f"{r.get('factor')}: {r.get('value')}" for r in (s.reasons or [])[:3]])

            # Google calendar render link
            gcal_title = urllib.parse.quote(f"Muhurta: {category_display}")
            gcal_desc = urllib.parse.quote(s.explanation_text or "")
            gcal_loc = urllib.parse.quote(city_display)
            start_iso = str(s.start_utc).replace("-", "").replace(":", "").split(".")[0]
            end_iso = str(s.end_utc).replace("-", "").replace(":", "").split(".")[0]
            gcal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={gcal_title}&dates={start_iso}Z/{end_iso}Z&details={gcal_desc}&location={gcal_loc}"

            slot_block = (
                f"\n🌟 *Option #{s.rank}* • *Score: {s.score:.1f}/30*\n"
                f"⏰ *{start_str}* — *{end_str}*\n"
                f"🪐 *Alignments:* {reasons_summary}\n"
                f"📖 {s.explanation_text}\n"
                f"📅 [Add to Google Calendar]({gcal_url})"
            )
            msg_lines.append(slot_block)

        msg_lines.append("\n━━━━━━━━━━━━━━━━━━━")
        msg_lines.append("🪔 _Calculated deterministically using Lahiri Ayanamsa & Swiss Ephemeris._")

        final_msg = "\n".join(msg_lines)
        await send_telegram_message(chat_id, final_msg)

    except Exception as exc:
        logger.error("Failed to process Telegram Muhurta query", error=str(exc))
        await send_telegram_message(
            chat_id,
            "⚠️ An error occurred while calculating auspicious timings. Please ensure your query includes an activity and a city (e.g. *Car purchase in Bengaluru next Friday*).",
        )


async def run_telegram_bot_polling() -> None:
    """Long-polling loop for Telegram Bot."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token or token == "REPLACE_ME":
        logger.info("Telegram bot token not configured; polling disabled.")
        return

    logger.info("Starting Telegram Bot long-polling worker...")
    offset = 0

    while True:
        try:
            url = f"{TELEGRAM_API_BASE}{token}/getUpdates"
            params = {"offset": offset, "timeout": 20}
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("ok"):
                        updates = data.get("result", [])
                        for u in updates:
                            update_id = u.get("update_id", 0)
                            offset = max(offset, update_id + 1)
                            # Handle each update safely in background
                            asyncio.create_task(handle_update(u))
                elif resp.status_code == 409:
                    logger.warning("Telegram conflict: webhook may be active or another polling instance running.")
                    await asyncio.sleep(5)
                else:
                    logger.warning("Telegram getUpdates returned error status", status=resp.status_code)
                    await asyncio.sleep(3)
        except asyncio.CancelledError:
            logger.info("Telegram Bot polling stopped.")
            break
        except Exception as exc:
            logger.error("Error in Telegram Bot polling loop", error=str(exc))
            await asyncio.sleep(5)
