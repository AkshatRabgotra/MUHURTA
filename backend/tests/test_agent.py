"""Tests for LLM agent graph, confidence routing, clarification, advisory notes, and validator."""

from __future__ import annotations

import uuid
import pytest

from app.agent.graph import run_muhurta_agent
from app.agent.validator import (
    build_template_explanation,
    extract_mentioned_entities,
    validate_explanation,
)
from app.services.experiments import assign_prompt_variant


@pytest.mark.asyncio
async def test_agent_high_confidence_category():
    """Verify high confidence query (>= 0.75) routes directly to category engine."""
    raw_query = "Starting my new tech job next week, looking for an auspicious weekday morning"
    test_uid = str(uuid.uuid4())

    state = await run_muhurta_agent(
        raw_text=raw_query,
        user_id=test_uid,
        user_tz="Asia/Kolkata",
        prompt_variant="explain_v1",
        llm_provider="mock",
    )

    assert state.get("status") == "success"
    assert state.get("category") == "new_beginnings"
    assert state.get("basis") == "category"
    assert state.get("confidence", 0) >= 0.75
    assert len(state.get("slots", [])) <= 3
    assert len(state.get("slots", [])) > 0
    assert len(state.get("explanations", [])) == len(state.get("slots", []))


@pytest.mark.asyncio
async def test_agent_medium_confidence_clarification():
    """Verify medium confidence query (0.40 <= c < 0.75) generates clarification flow."""
    raw_query = "clarification_test ambiguous event next week"
    test_uid = str(uuid.uuid4())

    state = await run_muhurta_agent(
        raw_text=raw_query,
        user_id=test_uid,
        llm_provider="mock",
    )

    assert state.get("status") == "needs_clarification"
    clarification = state.get("clarification")
    assert clarification is not None
    assert "question" in clarification
    assert len(clarification.get("options", [])) >= 2


@pytest.mark.asyncio
async def test_agent_low_confidence_general_fallback():
    """Verify low confidence query (< 0.40) routes to general fallback and includes disclosure."""
    raw_query = "some completely unusual request that does not match standard keywords"
    test_uid = str(uuid.uuid4())

    state = await run_muhurta_agent(
        raw_text=raw_query,
        user_id=test_uid,
        llm_provider="mock",
    )

    assert state.get("status") == "success"
    assert state.get("basis") == "general_fallback"
    assert state.get("category") == "general"
    # Explanations must include disclosure
    exps = state.get("explanations", [])
    assert len(exps) > 0
    for exp in exps:
        assert "universal" in exp.lower() or "general" in exp.lower() or "auspicious" in exp.lower()


@pytest.mark.asyncio
async def test_agent_override_pandit_advisory():
    """Verify an override with requires_pandit_review includes advisory note."""
    marriage_query = "Looking for auspicious wedding dates next month in Bengaluru"
    test_uid = str(uuid.uuid4())

    state = await run_muhurta_agent(
        raw_text=marriage_query,
        user_id=test_uid,
        llm_provider="mock",
    )

    assert state.get("status") == "success"
    assert state.get("override") == "marriage"
    assert state.get("advisory_note") is not None
    assert "pandit" in state["advisory_note"].lower()


@pytest.mark.asyncio
async def test_agent_invalid_json_retry_flow():
    """Verify agent handles invalid JSON from LLM and retries cleanly."""
    raw_query = "test_invalid_json Please help schedule an agreement"
    test_uid = str(uuid.uuid4())

    state = await run_muhurta_agent(
        raw_text=raw_query,
        user_id=test_uid,
        llm_provider="mock",
    )

    assert state.get("retry_parse_count", 0) >= 1 or state.get("status") in ("success", "needs_clarification")


def test_validator_grounding():
    """Verify explanation validator detects hallucinated astrological entities."""
    reasons = [
        {"factor": "Nakshatra", "value": "Rohini", "points": 3.0},
        {"factor": "Choghadiya", "value": "Amrit", "points": 3.0},
        {"factor": "Tithi", "value": "Shukla Panchami", "points": 2.0},
    ]

    # Grounded explanation mentioning only present factors -> passes
    grounded_exp = "This slot is auspicious because the Moon is in Rohini nakshatra and the active Choghadiya is Amrit."
    is_valid, err = validate_explanation(grounded_exp, reasons)
    assert is_valid is True
    assert err is None

    # Hallucinated nakshatra (Pushya not in reasons) -> rejected
    hallucinated_exp = "The divine alignment of Pushya nakshatra and Amrit choghadiya ensures great success."
    is_valid, err = validate_explanation(hallucinated_exp, reasons)
    assert is_valid is False
    assert "Pushya" in (err or "")


def test_template_explanation_fallback():
    """Verify template explanation constructs valid sentences directly from reasons."""
    reasons = [
        {"factor": "Nakshatra", "value": "Hasta", "points": 2.0},
        {"factor": "Choghadiya", "value": "Shubh", "points": 3.0},
    ]
    template = build_template_explanation(reasons)
    assert "Hasta" in template
    assert "Shubh" in template
    assert "auspicious" in template


def test_experiment_variant_deterministic_assignment():
    """Verify experiment assignment is deterministic and balanced."""
    uid1 = uuid.UUID("11111111-1111-1111-1111-111111111111")
    uid2 = uuid.UUID("22222222-2222-2222-2222-222222222222")

    var1_a = assign_prompt_variant(uid1)
    var1_b = assign_prompt_variant(uid1)
    assert var1_a == var1_b
    assert var1_a in ("explain_v1", "explain_v2")

    variants = [assign_prompt_variant(uuid.uuid4()) for _ in range(50)]
    assert "explain_v1" in variants
    assert "explain_v2" in variants
