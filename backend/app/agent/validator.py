"""Deterministic explanation validator for astrological fact grounding."""

from __future__ import annotations

import re
from typing import Any

from app.services.panchang import CHOGHADIYA_ORDER, NAKSHATRAS, TITHI_NAMES

# All canonical astrological entities
ALL_NAKSHATRAS = set(NAKSHATRAS)
ALL_TITHIS = set(TITHI_NAMES) | {"Amavasya", "Purnima"}
ALL_CHOGHADIYAS = set(CHOGHADIYA_ORDER)


def extract_mentioned_entities(text: str) -> set[str]:
    """Find any canonical astrological entities (nakshatra, tithi, choghadiya) mentioned in text."""
    mentioned: set[str] = set()
    text_lower = text.lower()

    for name in ALL_NAKSHATRAS:
        # Match as whole word
        pattern = r"\b" + re.escape(name.lower()) + r"\b"
        if re.search(pattern, text_lower):
            mentioned.add(name)

    for name in ALL_TITHIS:
        pattern = r"\b" + re.escape(name.lower()) + r"\b"
        if re.search(pattern, text_lower):
            mentioned.add(name)

    for name in ALL_CHOGHADIYAS:
        pattern = r"\b" + re.escape(name.lower()) + r"\b"
        if re.search(pattern, text_lower):
            mentioned.add(name)

    return mentioned


def validate_explanation(explanation: str, reasons: list[dict[str, Any]]) -> tuple[bool, str | None]:
    """Verify that every astrological entity mentioned in the explanation appears in that slot's reasons.
    Returns (is_valid, failure_detail).
    """
    mentioned = extract_mentioned_entities(explanation)
    if not mentioned:
        # No specific astrological entities mentioned (or generic statements) -> valid
        return True, None

    # Collect allowed entities from slot reasons
    allowed_entities: set[str] = set()
    for r in reasons:
        val = str(r.get("value", ""))
        for part in val.split():
            clean_part = part.strip("(),.#")
            for cat in (ALL_NAKSHATRAS, ALL_TITHIS, ALL_CHOGHADIYAS):
                for canon in cat:
                    if canon.lower() == clean_part.lower():
                        allowed_entities.add(canon)
        # Also check whole value string
        for cat in (ALL_NAKSHATRAS, ALL_TITHIS, ALL_CHOGHADIYAS):
            for canon in cat:
                if canon.lower() in val.lower():
                    allowed_entities.add(canon)

    # Check for ungrounded mentions
    hallucinated = mentioned - allowed_entities
    if hallucinated:
        return False, f"Mentioned entities not in slot reasons: {', '.join(hallucinated)}"

    return True, None


def build_template_explanation(reasons: list[dict[str, Any]]) -> str:
    """Deterministic fallback explanation constructed strictly from slot reasons."""
    if not reasons:
        return "This time window meets auspicious criteria according to the Muhurta guidelines for your event."

    parts = [f"{r.get('factor', 'Factor')} {r.get('value', '')}" for r in reasons if r.get('points', 0) > 0]
    if parts:
        joined = ", ".join(parts)
        return (
            f"This time window is auspicious due to favorable alignment of {joined}. "
            "It provides a harmonious and positive period for your activity."
        )
    return "This time window has no conflicting astrological periods and aligns well with your schedule."
