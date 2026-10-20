"""Google Calendar slot booking endpoint."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.api.auth import get_current_user
from app.db.models import AnalyticsEvent, User
from app.db.session import get_db
from app.schemas.common import CalendarEventResponse
from app.services.calendar_service import add_slot_to_calendar

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["calendar"])


@router.post("/slots/{slot_id}/calendar", response_model=CalendarEventResponse)
async def add_slot_to_google_calendar(
    slot_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CalendarEventResponse:
    """Add an auspicious time slot to Google Calendar (idempotent, transactional).
    Also schedules a Telegram reminder 60 minutes prior to event start.
    """
    cal_event, reminder = await add_slot_to_calendar(slot_id, current_user.id, db)

    # Record analytics event: slot_added_to_calendar
    analytics_ev = AnalyticsEvent(
        id=uuid.uuid4(),
        user_id=current_user.id,
        name="slot_added_to_calendar",
        props={
            "slot_id": str(slot_id),
            "calendar_event_id": str(cal_event.id),
            "google_event_id": cal_event.google_event_id,
        },
    )
    db.add(analytics_ev)
    await db.commit()

    return CalendarEventResponse(
        calendar_event_id=cal_event.id,
        google_event_id=cal_event.google_event_id,
        message="Slot successfully scheduled in Google Calendar and reminder configured.",
    )
