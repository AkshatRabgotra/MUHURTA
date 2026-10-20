"""LangGraph agent nodes and state definitions implementing category-based Muhurta."""

from __future__ import annotations

import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, TypedDict
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, ValidationError
import structlog

from app.agent.llm import get_llm_provider
from app.agent.validator import build_template_explanation, validate_explanation
from app.services.geocoding import geocode_location
from app.services.muhurta_rules import get_rules_registry, rank_slots, resolve_profile
from app.services.panchang import TimeWindow, get_day_windows

logger = structlog.get_logger(__name__)
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


# ── State Definition ─────────────────────────────────────────────────────────

class AgentState(TypedDict, total=False):
    raw_text: str
    user_tz: str
    default_city: str | None
    user_id: str | None
    prompt_variant: str
    llm_provider: str
    explicit_category: str | None

    constraints: dict[str, Any]
    is_muhurta_request: bool
    category: str
    override: str | None
    confidence: float
    basis: str  # "category" | "general_fallback"
    runner_up_category: str | None
    advisory_note: str | None
    shortage_reason: str | None
    clarification: dict[str, Any] | None

    location_name: str
    lat: float
    lon: float
    resolved_tz: str

    candidate_windows: list[Any]
    slots: list[dict[str, Any]]
    explanations: list[str]

    status: str  # "success" | "out_of_scope" | "needs_clarification" | "error"
    message: str | None

    retry_parse_count: int
    retry_explain_count: int

    tokens_in: int
    tokens_out: int
    latency_ms: int


# ── Pydantic Schema for Intent Parsing ───────────────────────────────────────

class ClassifyAndParseSchema(BaseModel):
    is_muhurta_request: bool = Field(description="False if malicious, harmful, or completely irrelevant")
    category: str = Field(description="One of the loaded category names")
    override: str | None = Field(default=None, description="One of the loaded override names or null")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    date_start: str = Field(description="ISO format start date YYYY-MM-DD")
    date_end: str = Field(description="ISO format end date YYYY-MM-DD")
    time_of_day_start: str | None = Field(default=None, description="HH:MM start time or null")
    time_of_day_end: str | None = Field(default=None, description="HH:MM end time or null")
    location_name: str | None = Field(default=None, description="City or place name")
    runner_up_category: str | None = Field(default=None, description="Second most likely category or null")


# ── Helper to Load Prompt ────────────────────────────────────────────────────

def load_prompt_template(filename: str) -> str:
    path = PROMPTS_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_dynamic_classification_prompt(user_tz_str: str, now_local: datetime, user_query: str) -> str:
    """Dynamically builds classification prompt injecting loaded categories and overrides."""
    registry = get_rules_registry()
    cat_descriptions: list[str] = []
    for name, cat in registry.categories.items():
        cat_descriptions.append(f"- {name}: {cat.display_name} — {cat.description}")

    ovr_descriptions: list[str] = []
    for name, ovr in registry.overrides.items():
        ovr_descriptions.append(f"- {name} (extends {ovr.extends}): {ovr.display_name}")

    prompt = f"""You are an expert intent parsing and category classification assistant for the Vedic Muhurta Planner.
Your job is to classify the user's natural language request into the best-matching category and extract scheduling constraints.

Current reference date in user's timezone ({user_tz_str}): {now_local.date().isoformat()} ({now_local.strftime('%A')}).

ALLOWED CATEGORIES:
{chr(10).join(cat_descriptions)}

ALLOWED SPECIFIC OVERRIDES (or null):
{chr(10).join(ovr_descriptions)}

INSTRUCTIONS:
1. Determine if this is a genuine Muhurta activity request. Set is_muhurta_request to false only if explicitly harmful or illegal.
2. Select the best category and optional override.
3. If confident in the category match (clear keywords or domain fit), assign confidence >= 0.75.
4. If ambiguous between two categories, assign confidence between 0.40 and 0.74, and provide runner_up_category.
5. If the request is vague or novel, select category "general" with confidence < 0.40.
6. Resolve relative dates (e.g. "tomorrow", "this weekend", "next week", "between 1 nov to 5 nov 2026") relative to current reference date {now_local.date().isoformat()}.
7. Extract time_of_day preferences (HH:MM) and location_name.
8. NEVER compute or output any astrological facts.

User request:
{user_query}
"""
    return prompt


# ── Node 1: classify_and_parse ───────────────────────────────────────────────

async def classify_and_parse_node(state: AgentState) -> dict[str, Any]:
    """Classify user request into dynamic taxonomy and extract constraints using the LLM."""
    start_t = time.perf_counter()

    # If explicit category was provided by user (e.g. from clarification flow), use it directly
    if state.get("explicit_category"):
        today = date.today()
        return {
            "is_muhurta_request": True,
            "category": state["explicit_category"],
            "override": None,
            "confidence": 1.0,
            "basis": "category",
            "runner_up_category": None,
            "constraints": {
                "date_start": (today + timedelta(days=1)).isoformat(),
                "date_end": (today + timedelta(days=7)).isoformat(),
            },
            "location_name": state.get("default_city") or "Bengaluru",
        }

    user_tz_str = state.get("user_tz", "Asia/Kolkata")
    user_tz = ZoneInfo(user_tz_str)
    now_local = datetime.now(user_tz)

    prompt = build_dynamic_classification_prompt(user_tz_str, now_local, state.get("raw_text", ""))
    provider = get_llm_provider(state.get("llm_provider"))
    retry_count = state.get("retry_parse_count", 0)

    try:
        res = await provider.complete(
            messages=[{"role": "user", "content": prompt}],
            json_schema=ClassifyAndParseSchema.model_json_schema(),
        )
        elapsed_ms = int((time.perf_counter() - start_t) * 1000)

        clean_text = res.text.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.strip("`")
            if clean_text.startswith("json"):
                clean_text = clean_text[4:].strip()

        data = json.loads(clean_text)
        validated = ClassifyAndParseSchema.model_validate(data)

        return {
            "is_muhurta_request": validated.is_muhurta_request,
            "category": validated.category,
            "override": validated.override,
            "confidence": validated.confidence,
            "runner_up_category": validated.runner_up_category,
            "constraints": {
                "date_start": validated.date_start,
                "date_end": validated.date_end,
                "time_of_day_start": validated.time_of_day_start,
                "time_of_day_end": validated.time_of_day_end,
                "location_name": validated.location_name,
            },
            "location_name": validated.location_name or state.get("default_city") or "Bengaluru",
            "tokens_in": state.get("tokens_in", 0) + res.tokens_in,
            "tokens_out": state.get("tokens_out", 0) + res.tokens_out,
            "latency_ms": state.get("latency_ms", 0) + elapsed_ms,
        }

    except (json.JSONDecodeError, ValidationError, Exception) as exc:
        elapsed_ms = int((time.perf_counter() - start_t) * 1000)
        logger.warning("classify_and_parse failed", error=str(exc), retry_count=retry_count)
        if retry_count < 1:
            return {
                "retry_parse_count": retry_count + 1,
                "tokens_in": state.get("tokens_in", 0),
                "tokens_out": state.get("tokens_out", 0),
                "latency_ms": state.get("latency_ms", 0) + elapsed_ms,
            }
        else:
            return {
                "status": "needs_clarification",
                "message": "We could not clearly parse your dates or intent. Please provide more details about your target event and timing.",
                "tokens_in": state.get("tokens_in", 0),
                "tokens_out": state.get("tokens_out", 0),
                "latency_ms": state.get("latency_ms", 0) + elapsed_ms,
            }


# ── Node 2: route_by_confidence ──────────────────────────────────────────────

async def route_by_confidence_node(state: AgentState) -> dict[str, Any]:
    """Deterministic routing node evaluating confidence thresholds."""
    if not state.get("is_muhurta_request", True):
        return {
            "status": "out_of_scope",
            "message": "This request appears outside the scope of traditional auspicious timing calculation.",
        }

    conf = state.get("confidence", 1.0)
    registry = get_rules_registry()

    # High confidence: proceed directly with category rules
    if conf >= 0.75:
        return {
            "basis": "category",
        }

    # Medium confidence: ambiguous between top category and runner-up
    if 0.40 <= conf < 0.75:
        cat1 = state.get("category", "general")
        cat2 = state.get("runner_up_category", "general") or "general"
        model1 = registry.categories.get(cat1) or registry.categories.get("general")
        model2 = registry.categories.get(cat2) or registry.categories.get("general")

        clarification_data = {
            "question": f"Which best describes your event?",
            "options": [
                {
                    "category": model1.category if model1 else cat1,
                    "label": model1.display_name if model1 else cat1,
                    "description": model1.description if model1 else "",
                },
                {
                    "category": model2.category if model2 else cat2,
                    "label": model2.display_name if model2 else cat2,
                    "description": model2.description if model2 else "",
                },
            ],
        }
        return {
            "status": "needs_clarification",
            "clarification": clarification_data,
            "message": "Please clarify the nature of your event to apply the most accurate Vedic timing rules.",
        }

    # Low confidence (< 0.40): fallback to universal general profile
    return {
        "category": "general",
        "override": None,
        "basis": "general_fallback",
    }


# ── Node 3: geocode ──────────────────────────────────────────────────────────

async def geocode_node(state: AgentState) -> dict[str, Any]:
    """Resolve location to lat/lon/timezone."""
    start_t = time.perf_counter()
    loc = state.get("location_name")
    default_c = state.get("default_city")
    lat, lon, tz = await geocode_location(loc, default_c)
    elapsed_ms = int((time.perf_counter() - start_t) * 1000)
    return {
        "lat": lat,
        "lon": lon,
        "resolved_tz": tz,
        "latency_ms": state.get("latency_ms", 0) + elapsed_ms,
    }


# ── Node 4: compute_slots (NO LLM) ───────────────────────────────────────────

async def compute_slots_node(state: AgentState) -> dict[str, Any]:
    """Deterministic slot scoring and ranking engine using resolved category profile."""
    start_t = time.perf_counter()
    constraints = state.get("constraints", {})
    category = state.get("category", "general")
    override = state.get("override")
    lat = state.get("lat", 12.9716)
    lon = state.get("lon", 77.5946)
    resolved_tz = state.get("resolved_tz", "Asia/Kolkata")

    # Resolve layered profile
    profile = resolve_profile(category, override)
    advisory_note = profile.advisory_note

    # Date range
    d_start_str = constraints.get("date_start")
    d_end_str = constraints.get("date_end")

    try:
        start_date = date.fromisoformat(d_start_str) if d_start_str else date.today() + timedelta(days=1)
        end_date = date.fromisoformat(d_end_str) if d_end_str else start_date + timedelta(days=6)
    except Exception:
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=6)

    # Max range safeguard: 30 days
    if (end_date - start_date).days > 30:
        end_date = start_date + timedelta(days=30)
    if end_date < start_date:
        end_date = start_date + timedelta(days=6)

    all_windows: list[TimeWindow] = []
    curr = start_date
    while curr <= end_date:
        windows = get_day_windows(curr, lat, lon, resolved_tz)
        all_windows.extend(windows)
        curr += timedelta(days=1)

    ranked, shortage_reason = rank_slots(all_windows, constraints, profile, top_n=3)

    serializable_slots: list[dict[str, Any]] = []
    for s in ranked:
        serializable_slots.append({
            "start_utc": s.window.start_utc.isoformat(),
            "end_utc": s.window.end_utc.isoformat(),
            "score": s.total_score,
            "rank": s.rank,
            "reasons": [
                {"factor": r.factor, "value": r.value, "points": r.points}
                for r in s.reasons
            ],
            "choghadiya": s.window.choghadiya,
            "tithi": f"{s.window.panchang.paksha} {s.window.panchang.tithi_name}",
            "nakshatra": s.window.panchang.nakshatra_name,
            "weekday": s.window.panchang.vara,
        })

    elapsed_ms = int((time.perf_counter() - start_t) * 1000)
    return {
        "slots": serializable_slots,
        "advisory_note": advisory_note,
        "shortage_reason": shortage_reason,
        "latency_ms": state.get("latency_ms", 0) + elapsed_ms,
    }


# ── Node 5: explain ──────────────────────────────────────────────────────────

async def explain_node(state: AgentState) -> dict[str, Any]:
    """Generate grounded 2 to 3 sentence explanation per slot."""
    start_t = time.perf_counter()
    slots = state.get("slots", [])
    if not slots:
        return {"explanations": []}

    basis = state.get("basis", "category")
    advisory_note = state.get("advisory_note")

    variant = state.get("prompt_variant", "explain_v1")
    prompt_filename = f"{variant}.txt" if variant in ("explain_v1", "explain_v2") else "explain_v1.txt"
    template = load_prompt_template(prompt_filename)

    slots_lines: list[str] = []
    for s in slots:
        reasons_desc = ", ".join(f"{r['factor']}: {r['value']} (+{r['points']} pts)" for r in s.get("reasons", []))
        slots_lines.append(f"Slot #{s['rank']} ({s['start_utc']}): Reasons: [{reasons_desc}]")

    prompt = template.replace("{slots_data}", "\n".join(slots_lines))
    if basis == "general_fallback":
        prompt += "\n\nNOTE: Basis is 'general_fallback'. You MUST state plainly in each explanation that timing is based on general auspicious factors rather than rules specific to this activity."

    provider = get_llm_provider(state.get("llm_provider"))
    res = await provider.complete(
        messages=[{"role": "user", "content": prompt}],
        json_schema={
            "type": "object",
            "properties": {
                "explanations": {
                    "type": "array",
                    "items": {"type": "string"},
                }
            },
            "required": ["explanations"],
        },
    )

    elapsed_ms = int((time.perf_counter() - start_t) * 1000)
    explanations: list[str] = []

    try:
        clean = res.text.strip()
        if clean.startswith("```"):
            clean = clean.strip("`")
            if clean.startswith("json"):
                clean = clean[4:].strip()
        data = json.loads(clean)
        explanations = data.get("explanations", [])
    except Exception as exc:
        logger.warning("Failed to parse explanation LLM response, using raw text", error=str(exc))
        explanations = [res.text]

    while len(explanations) < len(slots):
        idx = len(explanations)
        prefix = "Timing is based on general auspicious factors. " if basis == "general_fallback" else ""
        explanations.append(prefix + build_template_explanation(slots[idx].get("reasons", [])))

    return {
        "explanations": explanations[: len(slots)],
        "tokens_in": state.get("tokens_in", 0) + res.tokens_in,
        "tokens_out": state.get("tokens_out", 0) + res.tokens_out,
        "latency_ms": state.get("latency_ms", 0) + elapsed_ms,
    }


# ── Node 6: validate_explanation ─────────────────────────────────────────────

async def validate_explanation_node(state: AgentState) -> dict[str, Any]:
    """Verify that every astrological entity mentioned appears in that slot's reasons."""
    slots = state.get("slots", [])
    explanations = state.get("explanations", [])
    retry_count = state.get("retry_explain_count", 0)
    basis = state.get("basis", "category")

    has_invalid = False
    cleaned_explanations: list[str] = list(explanations)

    for i, slot in enumerate(slots):
        exp = explanations[i] if i < len(explanations) else ""
        is_valid, reason = validate_explanation(exp, slot.get("reasons", []))
        if not is_valid:
            has_invalid = True
            if retry_count >= 1:
                prefix = "Timing is based on general auspicious factors. " if basis == "general_fallback" else ""
                cleaned_explanations[i] = prefix + build_template_explanation(slot.get("reasons", []))

    if has_invalid and retry_count < 1:
        return {"retry_explain_count": retry_count + 1}

    return {
        "explanations": cleaned_explanations,
        "status": "success",
    }
