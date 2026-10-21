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
    parse_mode: str = "HTML",
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
            # Retry without HTML if parsing failed
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
                        f"✨ <b>Account Linked Successfully!</b> 🙏\n\n"
                        f"Namaste {first_name}! Your Telegram account is now connected to your Muhurta Planner profile (<b>{user.email}</b>).\n\n"
                        f"You will receive automatic alerts 1 hour before your scheduled auspicious windows.\n\n"
                        f"You can also ask me for auspicious timings anytime right here!",
                        parse_mode="HTML",
                    )
                    return
                else:
                    await send_telegram_message(
                        chat_id,
                        "⚠️ That link code is invalid or has expired. Please generate a fresh code from your Web Dashboard.",
                        parse_mode="HTML",
                    )
                    return

        # Regular /start or greeting
        welcome_text = (
            f"Namaste {first_name}! 🙏 Welcome to <b>Vedic Muhurta Planner</b> 🪔\n\n"
            f"I am your classical Vedic timing assistant, powered by the deterministic Swiss Ephemeris astronomical engine.\n\n"
            f"🌟 <b>Ask me directly for auspicious timings!</b>\n"
            f"Simply send your planned activity, for example:\n"
            f"• <code>Sign rental agreement this Friday morning in Bengaluru</code>\n"
            f"• <code>Buy a new car next week in Mumbai</code>\n"
            f"• <code>Griha Pravesh ceremony in Delhi next month</code>\n"
            f"• <code>Purchasing gold jewelry this weekend in Chennai</code>\n\n"
            f"🔗 <b>Link Your Web Profile:</b>\n"
            f"Send <code>/link &lt;code&gt;</code> using the code from your web dashboard to sync your consultations."
        )
        await send_telegram_message(chat_id, welcome_text, parse_mode="HTML")
        return

    # 2. Handle /link <code>
    if lower_text.startswith("/link"):
        parts = raw_text.split()
        if len(parts) < 2:
            await send_telegram_message(
                chat_id,
                "Please provide your 6-character link code from the web dashboard, like:\n<code>/link A1B2C3</code>",
                parse_mode="HTML",
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
                    f"✅ <b>Successfully Linked!</b> 🙏\n\n"
                    f"Your Telegram is now connected to <b>{user.email}</b>. All your consultations and 1-hour reminders will be synchronized.",
                    parse_mode="HTML",
                )
            else:
                await send_telegram_message(
                    chat_id,
                    "⚠️ Invalid or expired code. Please generate a new code from the web app.",
                    parse_mode="HTML",
                )
        return

    # 3. Natural Language Muhurta Query
    # Indicate typing while computing Swiss Ephemeris & Groq LLM
    await send_chat_action(chat_id, "typing")

    try:
        slots_data = []
        city_display = "Local Area"
        category_display = "Auspicious Timing"
        clarification = None
        shortage = None

        async with async_session_factory() as db:
            # Check if Telegram chat is linked to a registered web user
            q = select(User).where(User.telegram_chat_id == str(chat_id))
            res = await db.execute(q)
            user = res.scalar_one_or_none()
            linked_user_id = user.id if user else None

            # Run planner
            plan = await create_plan(
                user_id=linked_user_id,
                raw_text=raw_text,
                db=db,
            )

            city_display = plan.location_name or (user.default_city if user and user.default_city else "Bengaluru, India")
            category_display = (plan.override or plan.category or "Auspicious Timing").replace("_", " ").title()
            clarification = plan.clarification
            shortage = plan.shortage_reason

            for s in (plan.slots or []):
                slots_data.append({
                    "rank": s.rank,
                    "score": float(s.score) if s.score is not None else 0.0,
                    "start_utc": s.start_utc,
                    "end_utc": s.end_utc,
                    "reasons": s.reasons or [],
                    "explanation": s.explanation_text or "",
                })

        # If no auspicious slots found or needs clarification
        if not slots_data:
            if isinstance(clarification, dict) and clarification.get("question"):
                clarify_msg = clarification["question"]
            elif isinstance(clarification, str) and clarification.strip():
                clarify_msg = clarification.strip()
            elif shortage:
                clarify_msg = f"No ideal auspicious windows were found: {shortage}. Try expanding your search timeframe."
            else:
                clarify_msg = "Please mention your activity and preferred city."

            await send_telegram_message(
                chat_id,
                f"🪔 <b>More Details Needed</b>\n\n{clarify_msg}\n\n<i>Example:</i> <code>Car purchase in Mumbai next week</code>",
                parse_mode="HTML",
            )
            return

        # Format Top 3 slots response
        msg_lines = [
            f"🪔 <b>Vedic Muhurta Recommendations</b>",
            f"🎯 <b>Activity:</b> {category_display}",
            f"📍 <b>Location:</b> {city_display}",
            f"━━━━━━━━━━━━━━━━━━━━━━",
        ]

        for s in slots_data[:3]:
            start_dt = s["start_utc"]
            end_dt = s["end_utc"]

            if hasattr(start_dt, "strftime"):
                start_str = start_dt.strftime("%a, %b %d • %I:%M %p")
                end_str = end_dt.strftime("%I:%M %p")
                start_iso = start_dt.strftime("%Y%m%dT%H%M%SZ")
                end_iso = end_dt.strftime("%Y%m%dT%H%M%SZ")
            else:
                start_str = str(start_dt)
                end_str = str(end_dt)
                start_iso = ""
                end_iso = ""

            # Reasons summary
            reason_items = []
            for r in s.get("reasons", [])[:3]:
                if isinstance(r, dict):
                    factor = str(r.get("factor", "")).replace("_", " ").title()
                    val = str(r.get("value", "")).replace("_", " ").title()
                    reason_items.append(f"{factor}: <i>{val}</i>")
            reasons_summary = " • ".join(reason_items) if reason_items else "Harmonious Planetary Placement"

            # Clean explanation text
            explanation = (s.get("explanation") or "").strip()

            # Google Calendar link
            gcal_title = urllib.parse.quote(f"Muhurta: {category_display}")
            gcal_desc = urllib.parse.quote(explanation)
            gcal_loc = urllib.parse.quote(city_display)
            gcal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={gcal_title}&dates={start_iso}/{end_iso}&details={gcal_desc}&location={gcal_loc}"

            rank = s.get("rank", 1)
            score = s.get("score", 0.0)

            slot_block = (
                f"\n🌟 <b>Option #{rank}</b> • <b>Score: {score:.1f}/30</b>\n"
                f"⏰ <b>{start_str} — {end_str} UTC</b>\n"
                f"🪐 <b>Alignments:</b> {reasons_summary}\n"
                f"📖 {explanation}\n"
                f"📅 <a href=\"{gcal_url}\"><b>Add to Google Calendar ↗</b></a>"
            )
            msg_lines.append(slot_block)

        msg_lines.append("\n━━━━━━━━━━━━━━━━━━━━━━")
        msg_lines.append("🪔 <i>Calculated deterministically using Lahiri Ayanamsa & Swiss Ephemeris.</i>")

        final_msg = "\n".join(msg_lines)
        await send_telegram_message(chat_id, final_msg, parse_mode="HTML")

    except Exception as exc:
        logger.exception("Failed to process Telegram Muhurta query", error=str(exc))
        import html
        err_msg = html.escape(str(exc))
        await send_telegram_message(
            chat_id,
            f"⚠️ <b>Calculation Notice:</b>\n{err_msg}\n\nPlease try including an activity and city, for example:\n• <code>Car purchase in Mumbai next week</code>\n• <code>Rental agreement in Bengaluru this Friday</code>",
            parse_mode="HTML",
        )


async def run_telegram_bot_polling() -> None:
    """Long-polling loop for Telegram Bot."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token or token == "REPLACE_ME":
        logger.info("Telegram bot token not configured; polling disabled.")
        return

    # Clear any residual webhooks to ensure polling can run cleanly
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(f"{TELEGRAM_API_BASE}{token}/deleteWebhook")
    except Exception:
        pass

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
                    logger.warning("Telegram conflict (409): ensure only 1 uvicorn worker is running (--workers 1). Backing off.")
                    await asyncio.sleep(12)
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
