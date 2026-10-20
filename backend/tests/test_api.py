"""Comprehensive REST API and integration tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.config import get_settings
from app.db.models import AnalyticsEvent, CalendarEvent, Feedback, PlanRequest, Reminder, Slot
from tests.conftest import TEST_USER_ID, TestSessionFactory

settings = get_settings()


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """GET /api/v1/health returns service and DB health."""
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_dev_login(client: AsyncClient):
    """POST /api/v1/auth/dev-login logs in as test dev user in dev environment."""
    resp = await client.post("/api/v1/auth/dev-login")
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert "access_token" in resp.cookies


@pytest.mark.asyncio
async def test_get_and_patch_me(auth_client: AsyncClient):
    """GET and PATCH /api/v1/me."""
    resp = await auth_client.get("/api/v1/me")
    assert resp.status_code == 200
    me = resp.json()
    assert me["email"] == "testuser@example.com"
    assert me["timezone"] == "Asia/Kolkata"

    # Patch timezone and default city
    patch_resp = await auth_client.patch(
        "/api/v1/me",
        json={"timezone": "America/New_York", "default_city": "New York, USA"},
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["timezone"] == "America/New_York"
    assert updated["default_city"] == "New York, USA"


@pytest.mark.asyncio
async def test_create_and_view_plan(auth_client: AsyncClient):
    """POST /api/v1/plans runs agent and GET /api/v1/plans/{id} logs slots_viewed."""
    create_resp = await auth_client.post(
        "/api/v1/plans",
        json={"text": "I want to sign a rental agreement next week, mornings only in Bengaluru"},
    )
    assert create_resp.status_code == 200
    plan_data = create_resp.json()
    assert plan_data["category"] in ("property_construction", "money_business")
    assert len(plan_data["slots"]) <= 3
    assert len(plan_data["slots"]) > 0

    plan_id = plan_data["id"]

    # Retrieve single plan
    get_resp = await auth_client.get(f"/api/v1/plans/{plan_id}")
    assert get_resp.status_code == 200
    detail = get_resp.json()
    assert detail["id"] == plan_id

    # Verify slots_viewed analytics event was recorded in DB
    async with TestSessionFactory() as session:
        ev_q = select(AnalyticsEvent).where(
            AnalyticsEvent.plan_request_id == uuid.UUID(plan_id),
            AnalyticsEvent.name == "slots_viewed",
        )
        res = await session.execute(ev_q)
        event = res.scalar_one_or_none()
        assert event is not None


@pytest.mark.asyncio
async def test_calendar_transaction_and_idempotency(auth_client: AsyncClient):
    """POST /api/v1/slots/{id}/calendar creates CalendarEvent + Reminder atomically.
    Second call returns existing event without creating duplicate.
    """
    # 1. Create a plan first to obtain a slot
    plan_resp = await auth_client.post(
        "/api/v1/plans",
        json={"text": "Sign agreement next week"},
    )
    plan_data = plan_resp.json()
    slot_id = plan_data["slots"][0]["id"]

    # 2. Add to calendar
    cal_resp = await auth_client.post(f"/api/v1/slots/{slot_id}/calendar")
    assert cal_resp.status_code == 200
    cal_data = cal_resp.json()
    cal_id = cal_data["calendar_event_id"]

    # Verify in DB: CalendarEvent and Reminder both exist
    async with TestSessionFactory() as session:
        cal_obj = (await session.execute(select(CalendarEvent).where(CalendarEvent.id == uuid.UUID(cal_id)))).scalar_one_or_none()
        assert cal_obj is not None

        rem_obj = (await session.execute(select(Reminder).where(Reminder.calendar_event_id == uuid.UUID(cal_id)))).scalar_one_or_none()
        assert rem_obj is not None
        assert rem_obj.status == "pending"

    # 3. Double-click idempotency: second call returns the same calendar event
    cal_resp2 = await auth_client.post(f"/api/v1/slots/{slot_id}/calendar")
    assert cal_resp2.status_code == 200
    assert cal_resp2.json()["calendar_event_id"] == cal_id

    # Verify total CalendarEvents for this slot is still exactly 1
    async with TestSessionFactory() as session:
        count_res = await session.execute(
            select(CalendarEvent).where(CalendarEvent.slot_id == uuid.UUID(slot_id))
        )
        assert len(count_res.scalars().all()) == 1


@pytest.mark.asyncio
async def test_feedback_submission(auth_client: AsyncClient):
    """POST /api/v1/slots/{id}/feedback records user rating and analytics."""
    plan_resp = await auth_client.post(
        "/api/v1/plans",
        json={"text": "Starting a new job next Monday"},
    )
    slot_id = plan_resp.json()["slots"][0]["id"]

    fb_resp = await auth_client.post(
        f"/api/v1/slots/{slot_id}/feedback",
        json={"rating": 1, "comment": "Excellent auspicious timing!"},
    )
    assert fb_resp.status_code == 200
    fb_data = fb_resp.json()
    assert fb_data["rating"] == 1
    assert fb_data["comment"] == "Excellent auspicious timing!"

    # Verify analytics event
    async with TestSessionFactory() as session:
        ev = (await session.execute(
            select(AnalyticsEvent).where(AnalyticsEvent.name == "feedback_given")
        )).scalar_one_or_none()
        assert ev is not None


@pytest.mark.asyncio
async def test_telegram_link_and_webhook(auth_client: AsyncClient, client: AsyncClient):
    """POST /api/v1/me/telegram/link returns code and deep link, webhook links chat_id."""
    link_resp = await auth_client.post("/api/v1/me/telegram/link")
    assert link_resp.status_code == 200
    data = link_resp.json()
    code = data["code"]
    assert "t.me/" in data["deep_link"]

    # Simulate webhook update from Telegram user sending code
    webhook_payload = {
        "update_id": 1001,
        "message": {
            "chat": {"id": 55566677},
            "text": f"/start {code}",
        },
    }
    wh_resp = await client.post("/api/v1/telegram/webhook", json=webhook_payload)
    assert wh_resp.status_code == 200

    # Verify user profile has updated telegram_chat_id
    me_resp = await auth_client.get("/api/v1/me")
    assert me_resp.json()["telegram_chat_id"] == "55566677"


@pytest.mark.asyncio
async def test_analytics_funnel(auth_client: AsyncClient):
    """GET /api/v1/analytics/funnel aggregates conversion counts."""
    # Create a plan to populate analytics
    await auth_client.post("/api/v1/plans", json={"text": "Trip to London next month"})

    funnel_resp = await auth_client.get("/api/v1/analytics/funnel")
    assert funnel_resp.status_code == 200
    data = funnel_resp.json()
    assert "variants" in data
    assert len(data["variants"]) == 2
    variants = {v["prompt_variant"]: v for v in data["variants"]}
    assert "explain_v1" in variants
    assert "explain_v2" in variants


@pytest.mark.asyncio
async def test_internal_run_reminders(client: AsyncClient):
    """POST /api/v1/internal/run-reminders processes pending reminders with auth key."""
    # Unauthorized without header
    unauth_resp = await client.post("/api/v1/internal/run-reminders", headers={"X-Internal-Key": "wrong-key"})
    # If INTERNAL_API_KEY is REPLACE_ME, any key or none is accepted in dev, or 401 if configured
    if settings.INTERNAL_API_KEY != "REPLACE_ME":
        assert unauth_resp.status_code == 401

    # Call with correct key
    valid_key = settings.INTERNAL_API_KEY if settings.INTERNAL_API_KEY != "REPLACE_ME" else "any-key"
    resp = await client.post(
        "/api/v1/internal/run-reminders",
        headers={"X-Internal-Key": valid_key},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "processed" in data
    assert "sent" in data
    assert "failed" in data


@pytest.mark.asyncio
async def test_unmapped_analytics(auth_client: AsyncClient):
    """GET /api/v1/analytics/unmapped returns unmapped intent groups."""
    # Create an unmapped query
    await auth_client.post(
        "/api/v1/plans",
        json={"text": "completely unusual unique intent for analytics"},
    )
    resp = await auth_client.get("/api/v1/analytics/unmapped")
    assert resp.status_code == 200
    groups = resp.json()
    assert isinstance(groups, list)

