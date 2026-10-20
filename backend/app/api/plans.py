"""Plan creation and retrieval endpoints with in-memory per-user rate limiting."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from app.api.auth import get_current_user, get_optional_current_user
from app.core.errors import AppError, ErrorCode
from app.db.models import AnalyticsEvent, PlanRequest, Slot, User
from app.db.session import get_db
from app.schemas.plan import (
    PaginatedPlanResponse,
    PlanCreateRequest,
    PlanRequestSchema,
    SlotReasonSchema,
    SlotSchema,
)
from app.services.planner import create_plan

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["plans"])

# ── In-Memory Rate Limiter (10 req / min per user) ───────────────────────────
USER_REQUEST_TIMESTAMPS: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW_SECONDS = 60.0
RATE_LIMIT_MAX_REQUESTS = 10


def check_rate_limit(user_id: uuid.UUID) -> None:
    now = time.time()
    uid_str = str(user_id)
    timestamps = USER_REQUEST_TIMESTAMPS[uid_str]

    # Purge timestamps older than window
    valid_timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW_SECONDS]
    if len(valid_timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        raise AppError(
            code=ErrorCode.BAD_REQUEST,
            message="Rate limit exceeded: maximum 10 plan requests per minute allowed.",
            status_code=429,
        )
    valid_timestamps.append(now)
    USER_REQUEST_TIMESTAMPS[uid_str] = valid_timestamps


def _to_plan_schema(plan: PlanRequest) -> PlanRequestSchema:
    slots_out: list[SlotSchema] = []
    for s in plan.slots:
        reasons_list = [
            SlotReasonSchema(factor=r["factor"], value=str(r["value"]), points=float(r["points"]))
            for r in (s.reasons or [])
        ]
        slots_out.append(
            SlotSchema(
                id=s.id,
                plan_request_id=s.plan_request_id,
                start_utc=s.start_utc,
                end_utc=s.end_utc,
                score=s.score,
                reasons=reasons_list,
                explanation_text=s.explanation_text,
                rank=s.rank,
            )
        )
    slots_out.sort(key=lambda x: x.rank)

    return PlanRequestSchema(
        id=plan.id,
        user_id=plan.user_id,
        raw_text=plan.raw_text,
        parsed_constraints=plan.parsed_constraints,
        category=getattr(plan, "category", "general") or "general",
        override=getattr(plan, "override", None),
        confidence=getattr(plan, "confidence", 1.0) or 1.0,
        basis=getattr(plan, "basis", "category") or "category",
        runner_up_category=getattr(plan, "runner_up_category", None),
        advisory_note=getattr(plan, "advisory_note", None),
        shortage_reason=getattr(plan, "shortage_reason", None),
        clarification=getattr(plan, "clarification", None),
        event_type=getattr(plan, "event_type", None),
        location_name=plan.location_name,
        lat=plan.lat,
        lon=plan.lon,
        timezone=plan.timezone,
        prompt_variant=plan.prompt_variant,
        llm_provider=plan.llm_provider,
        status=plan.status,
        created_at=plan.created_at,
        slots=slots_out,
    )


@router.post("/plans", response_model=PlanRequestSchema)
async def create_new_plan(
    payload: PlanCreateRequest,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlanRequestSchema:
    """Create a new plan request: runs category agent and returns up to 3 scored auspicious slots.
    Unauthenticated guest users can calculate Muhurta without signing in.
    """
    user_id = current_user.id if current_user else None
    if user_id:
        check_rate_limit(user_id)
    plan = await create_plan(user_id, payload.text, db, explicit_category=payload.category)
    return _to_plan_schema(plan)


@router.get("/plans", response_model=PaginatedPlanResponse)
async def list_plans(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedPlanResponse:
    """List paginated history of plans for the current user."""
    offset = (page - 1) * page_size

    # Total count
    count_q = select(func.count()).select_from(PlanRequest).where(PlanRequest.user_id == current_user.id)
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch items
    items_q = (
        select(PlanRequest)
        .options(selectinload(PlanRequest.slots))
        .where(PlanRequest.user_id == current_user.id)
        .order_by(PlanRequest.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    res = await db.execute(items_q)
    plans = res.scalars().all()

    return PaginatedPlanResponse(
        items=[_to_plan_schema(p) for p in plans],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/plans/{plan_id}", response_model=PlanRequestSchema)
async def get_single_plan(
    plan_id: uuid.UUID,
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlanRequestSchema:
    """Get a single plan with slots. Accessible if anonymous or belongs to current user."""
    q = (
        select(PlanRequest)
        .options(selectinload(PlanRequest.slots))
        .where(PlanRequest.id == plan_id)
    )
    res = await db.execute(q)
    plan = res.scalar_one_or_none()
    if not plan:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Plan not found.", status_code=404)

    # If the plan was created by a registered user, only that user may view it
    if plan.user_id is not None and (not current_user or plan.user_id != current_user.id):
        raise AppError(code=ErrorCode.NOT_FOUND, message="Plan not found.", status_code=404)

    # Record analytics event: slots_viewed (if user logged in)
    if current_user:
        analytics_ev = AnalyticsEvent(
            id=uuid.uuid4(),
            user_id=current_user.id,
            plan_request_id=plan.id,
            name="slots_viewed",
            props={"slots_count": len(plan.slots)},
        )
        db.add(analytics_ev)
        await db.commit()

    return _to_plan_schema(plan)
