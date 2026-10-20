"""Planner service orchestrating the category agent, database persistence, and analytics."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent.graph import run_muhurta_agent
from app.config import get_settings
from app.db.models import AnalyticsEvent, PlanRequest, Slot, User
from app.services.experiments import assign_prompt_variant

settings = get_settings()


async def create_plan(
    user_id: uuid.UUID | None,
    raw_text: str,
    db: AsyncSession,
    explicit_category: str | None = None,
) -> PlanRequest:
    """Orchestrate category classification, astronomical computation, and explanation generation,
    then persist the PlanRequest and Slots into the database.
    """
    user = None
    if user_id:
        user_res = await db.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one_or_none()

    user_tz = user.timezone if user else "Asia/Kolkata"
    default_city = user.default_city if user else "Bengaluru, India"

    # Track clarification answered if explicit category provided
    if explicit_category:
        db.add(
            AnalyticsEvent(
                id=uuid.uuid4(),
                user_id=user_id,
                name="clarification_answered",
                props={"chosen_category": explicit_category, "raw_text": raw_text[:100]},
            )
        )

    prompt_variant = assign_prompt_variant(user_id)
    provider_name = settings.LLM_PROVIDER

    state = await run_muhurta_agent(
        raw_text=raw_text,
        user_id=str(user_id) if user_id else "guest",
        user_tz=user_tz,
        default_city=default_city,
        prompt_variant=prompt_variant,
        llm_provider=provider_name,
        explicit_category=explicit_category,
    )

    plan_status = state.get("status", "completed")
    if plan_status not in ("out_of_scope", "needs_clarification", "error"):
        plan_status = "completed"

    plan_req = PlanRequest(
        id=uuid.uuid4(),
        user_id=user_id,
        raw_text=raw_text,
        parsed_constraints=state.get("constraints"),
        category=state.get("category", "general"),
        override=state.get("override"),
        confidence=float(state.get("confidence", 1.0)),
        basis=state.get("basis", "category"),
        runner_up_category=state.get("runner_up_category"),
        advisory_note=state.get("advisory_note"),
        shortage_reason=state.get("shortage_reason"),
        clarification=state.get("clarification"),
        event_type=state.get("override") or state.get("category", "general"),
        location_name=state.get("location_name"),
        lat=state.get("lat"),
        lon=state.get("lon"),
        timezone=state.get("resolved_tz", user_tz),
        prompt_variant=prompt_variant,
        llm_provider=provider_name,
        llm_latency_ms=state.get("latency_ms"),
        tokens_in=state.get("tokens_in"),
        tokens_out=state.get("tokens_out"),
        status=plan_status,
    )
    db.add(plan_req)
    await db.flush()

    slots_data = state.get("slots", [])
    explanations = state.get("explanations", [])

    for i, s_dict in enumerate(slots_data):
        explanation_text = explanations[i] if i < len(explanations) else None
        slot_obj = Slot(
            id=uuid.uuid4(),
            plan_request_id=plan_req.id,
            start_utc=datetime.fromisoformat(s_dict["start_utc"]),
            end_utc=datetime.fromisoformat(s_dict["end_utc"]),
            score=s_dict["score"],
            reasons=s_dict.get("reasons"),
            explanation_text=explanation_text,
            rank=s_dict.get("rank", i + 1),
        )
        db.add(slot_obj)

    analytics_ev = AnalyticsEvent(
        id=uuid.uuid4(),
        user_id=user_id,
        plan_request_id=plan_req.id,
        name="request_created",
        props={
            "category": state.get("category"),
            "override": state.get("override"),
            "basis": state.get("basis"),
            "confidence": state.get("confidence"),
            "prompt_variant": prompt_variant,
            "slots_count": len(slots_data),
            "status": plan_status,
        },
    )
    db.add(analytics_ev)
    await db.commit()

    q = (
        select(PlanRequest)
        .options(selectinload(PlanRequest.slots))
        .where(PlanRequest.id == plan_req.id)
    )
    result = await db.execute(q)
    return result.scalar_one()
