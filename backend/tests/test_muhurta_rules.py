"""Unit tests for Muhurta rules, scoring, profile merging, and slot ranking."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
import pytest

from app.services.muhurta_rules import (
    load_rules,
    rank_slots,
    resolve_profile,
    score_slot,
)
from app.services.panchang import PanchangSnapshot, TimeWindow


def _make_dummy_window(
    dt_local: datetime,
    vara: str = "Monday",
    nakshatra: str = "Rohini",
    choghadiya: str = "Amrit",
    tithi_number: int = 5,
    tithi_name: str = "Panchami",
    paksha: str = "Shukla",
    is_rahu_kalam: bool = False,
) -> TimeWindow:
    utc = dt_local.astimezone(timezone.utc)
    snap = PanchangSnapshot(
        dt_utc=utc,
        sun_sid_lon=0.0,
        moon_sid_lon=0.0,
        tithi_number=tithi_number,
        tithi_name=tithi_name,
        paksha=paksha,
        nakshatra_number=4,
        nakshatra_name=nakshatra,
        nakshatra_pada=1,
        yoga_number=1,
        yoga_name="Vishkambha",
        karana_name="Bava",
        vara=vara,
        sunrise_utc=utc - timedelta(hours=3),
        sunset_utc=utc + timedelta(hours=9),
    )
    return TimeWindow(
        start_utc=utc,
        end_utc=utc + timedelta(minutes=30),
        start_local=dt_local,
        end_local=dt_local + timedelta(minutes=30),
        panchang=snap,
        choghadiya=choghadiya,
        is_rahu_kalam=is_rahu_kalam,
    )


def test_load_rules_and_validation():
    """Verify loading of universal, nakshatra classes, categories, and overrides."""
    reg = load_rules()
    assert len(reg.classes) == 7
    assert "dhruva" in reg.classes
    assert "Rohini" in reg.classes["dhruva"]
    assert "categories" in reg.__dict__
    assert len(reg.categories) == 8
    assert len(reg.overrides) == 4
    assert "marriage" in reg.overrides
    assert reg.overrides["marriage"].advisory is not None
    assert reg.overrides["marriage"].advisory.requires_pandit_review is True


def test_resolve_profile_merge_order():
    """Verify merge order: universal -> category -> override.

    - hard_avoid: union across all layers
    - soft_avoid and preferred: sum points per key
    - weights: later layers replace earlier
    - advisory: taken from override only
    """
    profile = resolve_profile("property_construction", override="griha_pravesh")

    # 1. hard_avoid union: universal includes tithi 30 and tikshna nakshatras;
    # griha_pravesh adds tithis [4, 8, 9, 14, 30]
    assert profile.hard_avoid_rahu is True
    assert 30 in profile.hard_avoid_tithis
    assert 4 in profile.hard_avoid_tithis
    assert 8 in profile.hard_avoid_tithis
    assert "tikshna" in profile.hard_avoid_nakshatra_classes

    # 2. preferred points: property_construction preferred dhruva: 4, griha_pravesh preferred dhruva: 3 -> sum is 7
    assert profile.preferred_nakshatra_classes.get("dhruva") == 7

    # 3. advisory note should be present from override
    assert profile.requires_pandit_review is True
    assert profile.advisory_note is not None
    assert "confirm with a pandit" in profile.advisory_note.lower()


def test_score_slot_nakshatra_class_and_weights():
    """Verify scoring looks up nakshatra class and awards category preferred points."""
    profile = resolve_profile("new_beginnings")
    tz = ZoneInfo("Asia/Kolkata")
    dt = datetime(2024, 4, 15, 10, 0, tzinfo=tz)  # Monday

    # Rohini is dhruva class (preferred 3 in new_beginnings, wt=1.5 -> 4.5 pts)
    # Monday is preferred 1 (wt=1.0 -> 1.0 pt)
    # Amrit is preferred 3 (wt=2.0 -> 6.0 pts)
    # Panchami (5) is preferred 2 (wt=1.0 -> 2.0 pts)
    # Total = 4.5 + 1.0 + 6.0 + 2.0 = 13.5
    w = _make_dummy_window(dt, vara="Monday", nakshatra="Rohini", choghadiya="Amrit", tithi_number=5)
    scored = score_slot(w, profile)

    assert not scored.is_rejected
    assert scored.total_score == 13.5
    factors = {r.factor: r.points for r in scored.reasons}
    assert factors["Nakshatra"] == 4.5
    assert factors["Choghadiya"] == 6.0


def test_score_slot_hard_avoid():
    """Verify slot is rejected outright during Rahu Kalam, Amavasya, or tikshna nakshatras."""
    profile = resolve_profile("new_beginnings")
    tz = ZoneInfo("Asia/Kolkata")
    dt = datetime(2024, 4, 15, 10, 0, tzinfo=tz)

    # 1. Rahu Kalam
    w_rahu = _make_dummy_window(dt, is_rahu_kalam=True)
    scored = score_slot(w_rahu, profile)
    assert scored.is_rejected is True
    assert "Rahu Kalam" in (scored.rejected_reason or "")

    # 2. Amavasya (tithi 30 from universal rule)
    w_tithi = _make_dummy_window(dt, tithi_number=30, tithi_name="Amavasya")
    scored = score_slot(w_tithi, profile)
    assert scored.is_rejected is True
    assert "30" in (scored.rejected_reason or "")

    # 3. Tikshna class nakshatra (e.g. Moola)
    w_moola = _make_dummy_window(dt, nakshatra="Moola")
    scored = score_slot(w_moola, profile)
    assert scored.is_rejected is True
    assert "Moola" in (scored.rejected_reason or "")


def test_rank_slots_spacing_requirement():
    """Enforces at least 2 hours between returned top 3 slots."""
    profile = resolve_profile("property_construction")
    tz = ZoneInfo("Asia/Kolkata")
    base_time = datetime(2024, 4, 15, 9, 0, tzinfo=tz)

    windows = []
    for i in range(8):
        t = base_time + timedelta(minutes=i * 30)
        nak = "Rohini" if i < 4 else "Uttara Phalguni"
        windows.append(_make_dummy_window(t, vara="Monday", nakshatra=nak, choghadiya="Amrit"))

    constraints = {"time_of_day_start": "09:00", "time_of_day_end": "14:00"}
    ranked, shortage = rank_slots(windows, constraints, profile, top_n=3)

    assert len(ranked) <= 3
    for i in range(len(ranked)):
        for j in range(i + 1, len(ranked)):
            diff_hours = abs((ranked[i].window.start_utc - ranked[j].window.start_utc).total_seconds()) / 3600.0
            assert diff_hours >= 2.0


def test_rank_slots_shortage_reason():
    """Verify shortage reason is populated when fewer than top_n slots are available."""
    profile = resolve_profile("general")
    tz = ZoneInfo("Asia/Kolkata")
    base_time = datetime(2024, 4, 15, 9, 0, tzinfo=tz)

    # Only 2 windows provided, both valid
    windows = [
        _make_dummy_window(base_time, nakshatra="Rohini", choghadiya="Amrit"),
        _make_dummy_window(base_time + timedelta(hours=3), nakshatra="Rohini", choghadiya="Amrit"),
    ]

    constraints = {"time_of_day_start": "09:00", "time_of_day_end": "14:00"}
    ranked, shortage = rank_slots(windows, constraints, profile, top_n=3)

    assert len(ranked) == 2
    assert shortage is not None
    assert "2" in shortage
    assert "widening the date range" in shortage
