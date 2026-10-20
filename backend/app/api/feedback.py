"""User feedback endpoint for Muhurta slots."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.api.auth import get_current_user
from app.core.errors import AppError, ErrorCode
from app.db.models import AnalyticsEvent, Feedback, Slot, User
from app.db.session import get_db
from app.schemas.common import FeedbackCreate, FeedbackResponse

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["feedback"])


@router.post("/slots/{slot_id}/feedback", response_model=FeedbackResponse)
async def submit_slot_feedback(
    slot_id: uuid.UUID,
    payload: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FeedbackResponse:
    """Submit thumbs up (1) or thumbs down (-1) feedback for an auspicious slot."""
    slot_res = await db.execute(select(Slot).where(Slot.id == slot_id))
    slot = slot_res.scalar_one_or_none()
    if not slot:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Slot not found.", status_code=404)

    feedback = Feedback(
        id=uuid.uuid4(),
        slot_id=slot_id,
        user_id=current_user.id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(feedback)
    await db.flush()

    # Record analytics event: feedback_given
    analytics_ev = AnalyticsEvent(
        id=uuid.uuid4(),
        user_id=current_user.id,
        name="feedback_given",
        props={"slot_id": str(slot_id), "rating": payload.rating},
    )
    db.add(analytics_ev)
    await db.commit()
    await db.refresh(feedback)

    return FeedbackResponse(
        id=feedback.id,
        slot_id=feedback.slot_id,
        user_id=feedback.user_id,
        rating=feedback.rating,
        comment=feedback.comment,
        created_at=feedback.created_at,
    )
