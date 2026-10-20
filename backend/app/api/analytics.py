"""Analytics funnel aggregation endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.api.auth import get_current_user
from app.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.db.models import AnalyticsEvent, PlanRequest, User
from app.db.session import get_db
from app.schemas.common import FunnelReportResponse, FunnelVariantStats
from app.schemas.plan import UnmappedRequestGroup

logger = structlog.get_logger(__name__)
settings = get_settings()
router = APIRouter(tags=["analytics"])


@router.get("/analytics/funnel", response_model=FunnelReportResponse)
async def get_funnel_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FunnelReportResponse:
    """Aggregate funnel counts and conversion rates per prompt_variant."""
    # Guard with ADMIN_EMAILS if non-dev
    if settings.ENV != "dev":
        admin_list = settings.admin_email_list
        if not admin_list or current_user.email not in admin_list:
            raise AppError(code=ErrorCode.FORBIDDEN, message="Admin privileges required.", status_code=403)

    variants = ["explain_v1", "explain_v2"]
    stats_list: list[FunnelVariantStats] = []

    for variant in variants:
        # Get count of request_created for this variant
        req_count_q = (
            select(func.count())
            .select_from(PlanRequest)
            .where(PlanRequest.prompt_variant == variant)
        )
        req_count = (await db.execute(req_count_q)).scalar() or 0

        # Subquery of plan_request IDs for this variant
        subq = select(PlanRequest.id).where(PlanRequest.prompt_variant == variant).scalar_subquery()

        # slots_viewed
        viewed_q = (
            select(func.count())
            .select_from(AnalyticsEvent)
            .where(AnalyticsEvent.name == "slots_viewed", AnalyticsEvent.plan_request_id.in_(subq))
        )
        slots_viewed = (await db.execute(viewed_q)).scalar() or 0

        # slot_added_to_calendar
        calendar_q = (
            select(func.count())
            .select_from(AnalyticsEvent)
            .where(AnalyticsEvent.name == "slot_added_to_calendar")
        )
        slot_added = (await db.execute(calendar_q)).scalar() or 0

        # reminder_sent
        rem_q = (
            select(func.count())
            .select_from(AnalyticsEvent)
            .where(AnalyticsEvent.name == "reminder_sent")
        )
        rem_sent = (await db.execute(rem_q)).scalar() or 0

        # feedback_given
        fb_q = (
            select(func.count())
            .select_from(AnalyticsEvent)
            .where(AnalyticsEvent.name == "feedback_given")
        )
        feedback_given = (await db.execute(fb_q)).scalar() or 0

        # Conversion rate
        conv_rate = round((slot_added / slots_viewed) * 100, 2) if slots_viewed > 0 else 0.0

        stats_list.append(
            FunnelVariantStats(
                prompt_variant=variant,
                request_created=req_count,
                slots_viewed=slots_viewed,
                slot_added_to_calendar=slot_added,
                reminder_sent=rem_sent,
                feedback_given=feedback_given,
                conversion_rate_viewed_to_calendar=conv_rate,
            )
        )

    return FunnelReportResponse(variants=stats_list)


@router.get("/analytics/unmapped", response_model=list[UnmappedRequestGroup])
async def get_unmapped_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[UnmappedRequestGroup]:
    """Return requests where basis == 'general_fallback' or confidence < 0.75,

    grouped by user intent, sorted by frequency descending.
    """
    if settings.ENV != "dev":
        admin_list = settings.admin_email_list
        if not admin_list or current_user.email not in admin_list:
            raise AppError(code=ErrorCode.FORBIDDEN, message="Admin privileges required.", status_code=403)

    stmt = (
        select(PlanRequest)
        .where(
            (PlanRequest.basis == "general_fallback") | (PlanRequest.confidence < 0.75)
        )
        .order_by(PlanRequest.created_at.desc())
    )
    result = await db.execute(stmt)
    unmapped_plans = result.scalars().all()

    # Group requests by normalized keyword/intent
    groups: dict[str, dict[str, Any]] = {}
    for plan in unmapped_plans:
        text = plan.raw_text.strip()
        # Normalization key: first 4 non-trivial words or raw lowercase text
        clean = " ".join([w for w in text.lower().split() if len(w) > 2][:4]) or text.lower()
        if clean not in groups:
            groups[clean] = {
                "keyword": clean,
                "count": 0,
                "newest_request": text,
                "last_created_at": plan.created_at,
                "sample_requests": [],
            }
        groups[clean]["count"] += 1
        if len(groups[clean]["sample_requests"]) < 5 and text not in groups[clean]["sample_requests"]:
            groups[clean]["sample_requests"].append(text)

    sorted_groups = sorted(groups.values(), key=lambda g: g["count"], reverse=True)
    return [UnmappedRequestGroup(**g) for g in sorted_groups]

