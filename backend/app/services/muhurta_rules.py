"""Muhurta scoring engine using Nakshatra class profiles, universal rules, and overrides."""

from __future__ import annotations

import functools
from dataclasses import dataclass, field
from datetime import time, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError
import yaml

from app.services.panchang import NAKSHATRAS, TimeWindow

RULES_DIR = Path(__file__).resolve().parent.parent / "rules"
CATEGORIES_DIR = RULES_DIR / "categories"
OVERRIDES_DIR = RULES_DIR / "overrides"


# ── Pydantic Validation Models for Rules Files ───────────────────────────────

class NakshatraClassesModel(BaseModel):
    classes: dict[str, list[str]]


class UniversalRulesModel(BaseModel):
    hard_avoid: dict[str, Any] = Field(default_factory=dict)
    soft_avoid: dict[str, Any] = Field(default_factory=dict)


class CategoryProfileModel(BaseModel):
    category: str
    display_name: str
    description: str
    hard_avoid: dict[str, Any] = Field(default_factory=dict)
    soft_avoid: dict[str, Any] = Field(default_factory=dict)
    preferred: dict[str, Any] = Field(default_factory=dict)
    weights: dict[str, float] = Field(default_factory=dict)


class AdvisoryModel(BaseModel):
    requires_pandit_review: bool = False
    note: str = ""


class OverrideProfileModel(BaseModel):
    override: str
    extends: str
    display_name: str
    hard_avoid: dict[str, Any] = Field(default_factory=dict)
    soft_avoid: dict[str, Any] = Field(default_factory=dict)
    preferred: dict[str, Any] = Field(default_factory=dict)
    weights: dict[str, float] = Field(default_factory=dict)
    advisory: AdvisoryModel | None = None


# ── Resolved Profile Dataclass ───────────────────────────────────────────────

@dataclass
class ResolvedProfile:
    category: str
    override: str | None
    display_name: str
    description: str
    hard_avoid_rahu: bool
    hard_avoid_choghadiya: set[str]
    hard_avoid_tithis: set[int]
    hard_avoid_nakshatra_classes: set[str]
    soft_avoid_tithis: dict[int, float]
    soft_avoid_nakshatra_classes: dict[str, float]
    preferred_nakshatra_classes: dict[str, float]
    preferred_weekdays: dict[str, float]
    preferred_choghadiya: dict[str, float]
    preferred_tithis: dict[int, float]
    weights: dict[str, float]
    advisory_note: str | None = None
    requires_pandit_review: bool = False


@dataclass
class SlotReason:
    factor: str
    value: str
    points: float


@dataclass
class ScoredSlot:
    window: TimeWindow
    total_score: float
    reasons: list[SlotReason] = field(default_factory=list)
    is_rejected: bool = False
    rejected_reason: str | None = None
    rank: int = 1


# ── Rule Loader and Registry ─────────────────────────────────────────────────

class RulesRegistry:
    """Singleton registry holding validated rule models and nakshatra-to-class mappings."""

    def __init__(self) -> None:
        self.nakshatra_to_class: dict[str, str] = {}
        self.class_to_nakshatras: dict[str, list[str]] = {}
        self.classes: dict[str, list[str]] = {}
        self.universal: UniversalRulesModel | None = None
        self.categories: dict[str, CategoryProfileModel] = {}
        self.overrides: dict[str, OverrideProfileModel] = {}
        self._load_and_validate_all()
        self.classes = self.class_to_nakshatras

    def _load_and_validate_all(self) -> None:
        # 1. Load nakshatra_classes.yaml
        nak_file = RULES_DIR / "nakshatra_classes.yaml"
        if not nak_file.exists():
            raise FileNotFoundError(f"Missing {nak_file}")
        with open(nak_file, "r", encoding="utf-8") as f:
            raw_nak = yaml.safe_load(f)
        validated_classes = NakshatraClassesModel.model_validate(raw_nak)

        # Validate that all 27 nakshatras are valid names
        known_set = set(NAKSHATRAS)
        mapped_count = 0
        for cls_name, nak_list in validated_classes.classes.items():
            self.class_to_nakshatras[cls_name] = nak_list
            for n in nak_list:
                # Allow variations like Moola/Mula, Swati/Svati
                clean_n = n.replace("Moola", "Mula").replace("Swati", "Svati")
                if clean_n not in known_set and n not in known_set:
                    raise ValueError(f"Unknown nakshatra name in {nak_file}: {n}")
                self.nakshatra_to_class[n] = cls_name
                self.nakshatra_to_class[clean_n] = cls_name
                mapped_count += 1

        # 2. Load universal.yaml
        uni_file = RULES_DIR / "universal.yaml"
        if not uni_file.exists():
            raise FileNotFoundError(f"Missing {uni_file}")
        with open(uni_file, "r", encoding="utf-8") as f:
            raw_uni = yaml.safe_load(f)
        self.universal = UniversalRulesModel.model_validate(raw_uni)

        # 3. Load categories/*.yaml
        if CATEGORIES_DIR.exists():
            for p in CATEGORIES_DIR.glob("*.yaml"):
                with open(p, "r", encoding="utf-8") as f:
                    raw_cat = yaml.safe_load(f)
                cat_model = CategoryProfileModel.model_validate(raw_cat)
                self.categories[cat_model.category] = cat_model

        # 4. Load overrides/*.yaml
        if OVERRIDES_DIR.exists():
            for p in OVERRIDES_DIR.glob("*.yaml"):
                with open(p, "r", encoding="utf-8") as f:
                    raw_ovr = yaml.safe_load(f)
                ovr_model = OverrideProfileModel.model_validate(raw_ovr)
                if ovr_model.extends not in self.categories:
                    raise ValueError(f"Override {ovr_model.override} extends unknown category {ovr_model.extends}")
                self.overrides[ovr_model.override] = ovr_model


_REGISTRY: RulesRegistry | None = None


def get_rules_registry() -> RulesRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = RulesRegistry()
    return _REGISTRY


def load_rules() -> RulesRegistry:
    """Public function to load and validate all rules."""
    return get_rules_registry()


# ── Profile Resolver ─────────────────────────────────────────────────────────

def resolve_profile(category_name: str, override_name: str | None = None, override: str | None = None) -> ResolvedProfile:
    """Merge in strict order: universal -> category -> override.
    - hard_avoid: union of all layers.
    - soft_avoid and preferred: sum points per key across layers.
    - weights: later layers replace earlier ones.
    - advisory: taken from the override only.
    """
    effective_override = override or override_name
    registry = get_rules_registry()

    # Fall back to general if category not found
    cat_model = registry.categories.get(category_name) or registry.categories.get("general")
    if not cat_model:
        raise ValueError(f"Category '{category_name}' not found and no general fallback available.")

    ovr_model = registry.overrides.get(effective_override) if effective_override else None

    # Base layers
    layers = [registry.universal, cat_model]
    if ovr_model:
        layers.append(ovr_model)

    # 1. Hard avoid union
    hard_rahu = False
    hard_choghadiya: set[str] = set()
    hard_tithis: set[int] = set()
    hard_nak_classes: set[str] = set()

    for layer in layers:
        ha = getattr(layer, "hard_avoid", {}) or {}
        if ha.get("rahu_kalam"):
            hard_rahu = True
        for c in ha.get("choghadiya", []):
            hard_choghadiya.add(str(c))
        for t in ha.get("tithis", []):
            hard_tithis.add(int(t))
        for nc in ha.get("nakshatra_classes", []):
            hard_nak_classes.add(str(nc))

    # 2. Soft avoid sum
    soft_tithis: dict[int, float] = {}
    soft_nak_classes: dict[str, float] = {}
    for layer in layers:
        sa = getattr(layer, "soft_avoid", {}) or {}
        for t, pts in sa.get("tithis", {}).items():
            soft_tithis[int(t)] = soft_tithis.get(int(t), 0.0) + float(pts)
        for nc, pts in sa.get("nakshatra_classes", {}).items():
            soft_nak_classes[str(nc)] = soft_nak_classes.get(str(nc), 0.0) + float(pts)

    # 3. Preferred sum
    pref_nak_classes: dict[str, float] = {}
    pref_weekdays: dict[str, float] = {}
    pref_choghadiya: dict[str, float] = {}
    pref_tithis: dict[int, float] = {}

    for layer in layers:
        pref = getattr(layer, "preferred", {}) or {}
        for nc, pts in pref.get("nakshatra_classes", {}).items():
            pref_nak_classes[str(nc)] = pref_nak_classes.get(str(nc), 0.0) + float(pts)
        for w, pts in pref.get("weekdays", {}).items():
            pref_weekdays[str(w)] = pref_weekdays.get(str(w), 0.0) + float(pts)
        for c, pts in pref.get("choghadiya", {}).items():
            pref_choghadiya[str(c)] = pref_choghadiya.get(str(c), 0.0) + float(pts)
        for t, pts in pref.get("tithis", {}).items():
            pref_tithis[int(t)] = pref_tithis.get(int(t), 0.0) + float(pts)

    # 4. Weights replacement (default -> category -> override)
    weights: dict[str, float] = {"nakshatra": 1.5, "weekday": 1.0, "choghadiya": 2.0, "tithi": 1.0}
    if cat_model.weights:
        weights.update(cat_model.weights)
    if ovr_model and ovr_model.weights:
        weights.update(ovr_model.weights)

    # 5. Advisory note from override
    advisory_note = None
    requires_pandit_review = False
    if ovr_model and ovr_model.advisory:
        advisory_note = ovr_model.advisory.note
        requires_pandit_review = ovr_model.advisory.requires_pandit_review

    display_name = ovr_model.display_name if ovr_model else cat_model.display_name

    return ResolvedProfile(
        category=cat_model.category,
        override=ovr_model.override if ovr_model else None,
        display_name=display_name,
        description=cat_model.description,
        hard_avoid_rahu=hard_rahu,
        hard_avoid_choghadiya=hard_choghadiya,
        hard_avoid_tithis=hard_tithis,
        hard_avoid_nakshatra_classes=hard_nak_classes,
        soft_avoid_tithis=soft_tithis,
        soft_avoid_nakshatra_classes=soft_nak_classes,
        preferred_nakshatra_classes=pref_nak_classes,
        preferred_weekdays=pref_weekdays,
        preferred_choghadiya=pref_choghadiya,
        preferred_tithis=pref_tithis,
        weights=weights,
        advisory_note=advisory_note,
        requires_pandit_review=requires_pandit_review,
    )


# ── Slot Scoring ─────────────────────────────────────────────────────────────

def score_slot(window: TimeWindow, profile: ResolvedProfile) -> ScoredSlot:
    """Score individual candidate time window according to resolved profile.
    Looks up Nakshatra class from nakshatra_classes.yaml.
    """
    registry = get_rules_registry()
    nak_name = window.panchang.nakshatra_name
    nak_class = registry.nakshatra_to_class.get(nak_name, "mishra")

    # 1. Hard avoids
    if profile.hard_avoid_rahu and window.is_rahu_kalam:
        return ScoredSlot(
            window=window,
            total_score=0.0,
            is_rejected=True,
            rejected_reason="Rahu Kalam period (inauspicious time)",
        )

    if window.panchang.tithi_number in profile.hard_avoid_tithis:
        return ScoredSlot(
            window=window,
            total_score=0.0,
            is_rejected=True,
            rejected_reason=f"Inauspicious Tithi: {window.panchang.tithi_name} (#{window.panchang.tithi_number})",
        )

    if window.choghadiya in profile.hard_avoid_choghadiya:
        return ScoredSlot(
            window=window,
            total_score=0.0,
            is_rejected=True,
            rejected_reason=f"Inauspicious Choghadiya: {window.choghadiya}",
        )

    if nak_class in profile.hard_avoid_nakshatra_classes:
        return ScoredSlot(
            window=window,
            total_score=0.0,
            is_rejected=True,
            rejected_reason=f"Inauspicious Nakshatra Class: {nak_class} ({nak_name})",
        )

    # 2. Scoring & Reasons
    total_score = 0.0
    reasons: list[SlotReason] = []
    w = profile.weights

    # Nakshatra class preferred & soft avoid
    nak_weight = float(w.get("nakshatra", 1.5))
    pref_nak_pts = profile.preferred_nakshatra_classes.get(nak_class, 0.0)
    soft_nak_pts = profile.soft_avoid_nakshatra_classes.get(nak_class, 0.0)
    net_nak_pts = pref_nak_pts + soft_nak_pts
    if net_nak_pts != 0:
        contrib = round(net_nak_pts * nak_weight, 2)
        total_score += contrib
        reasons.append(
            SlotReason(
                factor="Nakshatra",
                value=f"{nak_name} ({nak_class})",
                points=contrib,
            )
        )

    # Weekday preferred
    w_weight = float(w.get("weekday", 1.0))
    vara_pts = profile.preferred_weekdays.get(window.panchang.vara, 0.0)
    if vara_pts > 0:
        contrib = round(vara_pts * w_weight, 2)
        total_score += contrib
        reasons.append(
            SlotReason(
                factor="Weekday",
                value=window.panchang.vara,
                points=contrib,
            )
        )

    # Choghadiya preferred
    c_weight = float(w.get("choghadiya", 2.0))
    chog_pts = profile.preferred_choghadiya.get(window.choghadiya, 0.0)
    if chog_pts > 0:
        contrib = round(chog_pts * c_weight, 2)
        total_score += contrib
        reasons.append(
            SlotReason(
                factor="Choghadiya",
                value=window.choghadiya,
                points=contrib,
            )
        )

    # Tithi preferred & soft avoid
    t_weight = float(w.get("tithi", 1.0))
    pref_t_pts = profile.preferred_tithis.get(window.panchang.tithi_number, 0.0)
    soft_t_pts = profile.soft_avoid_tithis.get(window.panchang.tithi_number, 0.0)
    net_t_pts = pref_t_pts + soft_t_pts
    if net_t_pts != 0:
        contrib = round(net_t_pts * t_weight, 2)
        total_score += contrib
        reasons.append(
            SlotReason(
                factor="Tithi",
                value=f"{window.panchang.paksha} {window.panchang.tithi_name}",
                points=contrib,
            )
        )

    return ScoredSlot(
        window=window,
        total_score=round(total_score, 2),
        reasons=reasons,
        is_rejected=False,
    )


# ── Slot Ranking ─────────────────────────────────────────────────────────────

def rank_slots(
    windows: list[TimeWindow],
    constraints: dict[str, Any],
    profile: ResolvedProfile,
    top_n: int = 3,
) -> tuple[list[ScoredSlot], str | None]:
    """Filter candidate windows, score with resolved profile, and enforce at least 2 hours separation.
    Returns (selected_slots, shortage_reason). Never fabricates slots.
    """
    time_start_str = constraints.get("time_of_day_start")
    time_end_str = constraints.get("time_of_day_end")

    def parse_hhmm(s: str | None) -> time | None:
        if not s:
            return None
        parts = s.split(":")
        try:
            return time(int(parts[0]), int(parts[1]))
        except Exception:
            return None

    tod_start = parse_hhmm(time_start_str)
    tod_end = parse_hhmm(time_end_str)

    filtered_candidates: list[TimeWindow] = []
    for w in windows:
        slot_local_time = w.start_local.time()
        if tod_start and slot_local_time < tod_start:
            continue
        if tod_end and slot_local_time >= tod_end:
            continue
        filtered_candidates.append(w)

    scored: list[ScoredSlot] = []
    for w in filtered_candidates:
        s = score_slot(w, profile)
        if not s.is_rejected and s.total_score > 0:
            scored.append(s)

    scored.sort(key=lambda s: (-s.total_score, s.window.start_utc))

    selected: list[ScoredSlot] = []
    min_separation = timedelta(hours=2)

    for candidate in scored:
        if len(selected) >= top_n:
            break
        conflict = False
        for s in selected:
            gap = abs((candidate.window.start_utc - s.window.start_utc).total_seconds())
            if gap < min_separation.total_seconds():
                conflict = True
                break
        if not conflict:
            candidate.rank = len(selected) + 1
            selected.append(candidate)

    shortage_reason = None
    if len(selected) < top_n:
        if len(selected) == 0:
            shortage_reason = "No auspicious windows survived filters in this range. Try widening dates or removing time restrictions."
        else:
            shortage_reason = f"Few suitable windows in this date range ({len(selected)} found). Try widening the date range to find more options."

    return selected, shortage_reason
