"""Pydantic schemas for plan requests and time slots."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class ClarificationOption(BaseModel):
    category: str
    label: str
    description: str


class ClarificationSchema(BaseModel):
    question: str
    options: list[ClarificationOption]


class PlanCreateRequest(BaseModel):
    """User input text to create a new plan."""
    text: str = Field(..., min_length=3, max_length=1000, description="Natural language description of the event.")
    category: str | None = Field(default=None, description="Explicit category selection to bypass intent classification.")


class SlotReasonSchema(BaseModel):
    """A single scoring factor explaining why a slot gained or lost points."""
    factor: str
    value: str
    points: float


class SlotSchema(BaseModel):
    """A scored auspicious time slot."""
    id: uuid.UUID
    plan_request_id: uuid.UUID
    start_utc: datetime
    end_utc: datetime
    score: float
    reasons: list[SlotReasonSchema]
    explanation_text: str | None = None
    rank: int


class PlanRequestSchema(BaseModel):
    """A plan request containing up to 3 ranked slots."""
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    raw_text: str
    parsed_constraints: dict[str, Any] | None = None
    category: str = "general"
    override: str | None = None
    confidence: float = 1.0
    basis: str = "category"  # "category" | "general_fallback"
    runner_up_category: str | None = None
    advisory_note: str | None = None
    shortage_reason: str | None = None
    clarification: ClarificationSchema | dict[str, Any] | None = None
    event_type: str | None = None
    location_name: str | None = None
    lat: float | None = None
    lon: float | None = None
    timezone: str | None = None
    prompt_variant: str | None = None
    llm_provider: str | None = None
    status: str
    created_at: datetime
    slots: list[SlotSchema] = []


class PaginatedPlanResponse(BaseModel):
    items: list[PlanRequestSchema]
    total: int
    page: int
    page_size: int


class UnmappedRequestGroup(BaseModel):
    keyword: str
    count: int
    newest_request: str
    last_created_at: datetime
    sample_requests: list[str]
