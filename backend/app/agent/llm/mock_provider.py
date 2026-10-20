"""Deterministic Mock LLM Provider matching the category patch specification."""

from __future__ import annotations

import json
import re
import time
from datetime import date, datetime, timedelta
from typing import Any

from app.agent.llm.base import LLMProvider, LLMResult


class MockProvider(LLMProvider):
    """Deterministic provider simulating LLM completions without external API calls."""

    async def complete(
        self,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResult:
        start_t = time.perf_counter()
        all_text = " ".join(m.get("content", "") for m in messages).lower()

        # Check for test-induced invalid JSON simulation
        if "test_invalid_json" in all_text and "retry" not in all_text:
            elapsed_ms = int((time.perf_counter() - start_t) * 1000)
            return LLMResult(
                text="This is not valid JSON string",
                tokens_in=50,
                tokens_out=10,
                latency_ms=elapsed_ms,
            )

        # 1. Classify and Parse Intent
        if json_schema is not None or "classify_and_parse" in all_text or "is_muhurta_request" in all_text:
            today = date.today()
            start_d = today + timedelta(days=1)
            end_d = today + timedelta(days=7)

            user_part = all_text
            if "user request:" in all_text:
                user_part = all_text.split("user request:")[-1]

            # Out of scope check
            if any(w in user_part for w in ("malicious", "illegal", "kill", "harm", "unsupported_test_query")):
                parsed = {
                    "is_muhurta_request": False,
                    "category": "general",
                    "override": None,
                    "confidence": 0.0,
                    "date_start": start_d.isoformat(),
                    "date_end": end_d.isoformat(),
                    "time_of_day_start": None,
                    "time_of_day_end": None,
                    "location_name": "Bengaluru",
                    "runner_up_category": None,
                }
                elapsed_ms = int((time.perf_counter() - start_t) * 1000)
                return LLMResult(text=json.dumps(parsed), tokens_in=100, tokens_out=50, latency_ms=elapsed_ms)

            # Test hook for clarification flow
            if "test_ambiguous" in user_part or "clarification_test" in user_part:
                parsed = {
                    "is_muhurta_request": True,
                    "category": "money_business",
                    "override": None,
                    "confidence": 0.60,
                    "date_start": start_d.isoformat(),
                    "date_end": end_d.isoformat(),
                    "time_of_day_start": "09:00",
                    "time_of_day_end": "12:00",
                    "location_name": "Bengaluru",
                    "runner_up_category": "purchases",
                }
                elapsed_ms = int((time.perf_counter() - start_t) * 1000)
                return LLMResult(text=json.dumps(parsed), tokens_in=100, tokens_out=50, latency_ms=elapsed_ms)

            # Keyword classification per spec B1
            category = "general"
            override = None
            confidence = 0.2  # Unmatched default

            # Check overrides first
            if any(w in user_part for w in ("griha", "housewarming", "house-warming", "moving in")):
                category = "property_construction"
                override = "griha_pravesh"
                confidence = 0.95
            elif any(w in user_part for w in ("marriage", "wedding", "vivaha")):
                category = "relationships_family"
                override = "marriage"
                confidence = 0.95
            elif any(w in user_part for w in ("naming", "namakarana")):
                category = "relationships_family"
                override = "naming_ceremony"
                confidence = 0.95
            elif any(w in user_part for w in ("buy car", "buy bike", "purchase vehicle", "vehicle delivery")):
                category = "vehicle_travel"
                override = "vehicle_purchase"
                confidence = 0.95
            # Categories
            elif any(w in user_part for w in ("house", "flat", "rent", "plot", "lease", "agreement", "construction", "property")):
                category = "property_construction"
                confidence = 0.9
            elif any(w in user_part for w in ("car", "bike", "trip", "flight", "travel", "journey")):
                category = "vehicle_travel"
                confidence = 0.9
            elif any(w in user_part for w in ("job", "join", "start", "venture", "career", "interview", "first day")):
                category = "new_beginnings"
                confidence = 0.9
            elif any(w in user_part for w in ("contract", "deal", "money", "invest", "loan", "shop opening", "business")):
                category = "money_business"
                confidence = 0.9
            elif any(w in user_part for w in ("learn", "study", "course", "exam", "admission", "school", "college")):
                category = "education_learning"
                confidence = 0.9
            elif any(w in user_part for w in ("party", "anniversary", "birthday", "gathering", "reunion", "celebrat")):
                category = "relationships_family"
                confidence = 0.9
            elif any(w in user_part for w in ("gold", "appliance", "clothes", "jewelry", "buy", "purchase")):
                category = "purchases"
                confidence = 0.9

            # Parse explicit date ranges (e.g. "between 1 nov to 5 nov 2026")
            month_map = {
                "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
            }
            date_range_match = re.search(
                r"(\d{1,2})\s*([a-z]{3})[a-z]*\s*(?:to|-)\s*(\d{1,2})\s*([a-z]{3})?[a-z]*\s*(\d{4})?",
                user_part,
            )
            if date_range_match:
                d1 = int(date_range_match.group(1))
                m1_str = date_range_match.group(2)[:3]
                d2 = int(date_range_match.group(3))
                m2_str = (date_range_match.group(4) or m1_str)[:3]
                yr = int(date_range_match.group(5)) if date_range_match.group(5) else today.year
                m1 = month_map.get(m1_str, today.month)
                m2 = month_map.get(m2_str, m1)
                try:
                    start_d = date(yr, m1, d1)
                    end_d = date(yr, m2, d2)
                except Exception:
                    pass

            # Detect morning / afternoon / evening
            if "morning" in user_part:
                tod_start = "09:00"
                tod_end = "12:00"
            elif "afternoon" in user_part:
                tod_start = "12:00"
                tod_end = "16:00"
            elif "evening" in user_part:
                tod_start = "16:00"
                tod_end = "20:00"
            else:
                tod_start = None
                tod_end = None

            # Detect city if mentioned
            loc = "Bengaluru"
            for city in ("delhi", "mumbai", "chennai", "kolkata", "hyderabad", "pune", "london", "new york"):
                if city in user_part:
                    loc = city.title()
                    break

            parsed = {
                "is_muhurta_request": True,
                "category": category,
                "override": override,
                "confidence": confidence,
                "date_start": start_d.isoformat(),
                "date_end": end_d.isoformat(),
                "time_of_day_start": tod_start,
                "time_of_day_end": tod_end,
                "location_name": loc,
                "runner_up_category": "general" if confidence >= 0.75 else None,
            }

            elapsed_ms = int((time.perf_counter() - start_t) * 1000)
            return LLMResult(text=json.dumps(parsed), tokens_in=120, tokens_out=60, latency_ms=elapsed_ms)

        # 2. Explanation response
        # Extract structured reasons from the input message
        is_general_fallback = "general_fallback" in all_text

        slot_blocks = re.split(r"Slot\s+#?\d+:", all_text)
        explanations: list[str] = []

        if len(slot_blocks) > 1:
            for block in slot_blocks[1:]:
                factors = []
                for factor_match in re.finditer(r"(nakshatra|tithi|choghadiya|weekday):\s*([a-z0-9\s\(\)]+)", block):
                    clean_v = factor_match.group(2).split("(")[0].strip().title()
                    factors.append(f"{factor_match.group(1).title()} {clean_v}")

                prefix = "This timing is based on general auspicious factors rather than rules specific to this activity. " if is_general_fallback else ""
                if factors:
                    sentence = f"{prefix}This auspicious window aligns with favorable {', '.join(factors)}. It offers an auspicious Vedic alignment."
                else:
                    sentence = f"{prefix}This time window has positive planetary indicators according to Muhurta rules."
                explanations.append(sentence)

            result_obj = {"explanations": explanations}
            text = json.dumps(result_obj)
        else:
            text = json.dumps({
                "explanations": [
                    "This time window aligns with auspicious astrological influences according to the computed factors."
                ]
            })

        elapsed_ms = int((time.perf_counter() - start_t) * 1000)
        return LLMResult(text=text, tokens_in=250, tokens_out=80, latency_ms=elapsed_ms)
