"""Deterministic Vedic Panchang engine.

Pure functions, no I/O, no LLM.
Uses pyswisseph (Swiss Ephemeris with Lahiri ayanamsa) when available,
with an astronomical fallback when pyswisseph is not installed.
"""

from __future__ import annotations

import functools
import math
from dataclasses import asdict, dataclass
from datetime import date as dt_date
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

try:
    import swisseph as swe
    HAS_SWISSEPH = True
except ImportError:
    swe = None  # type: ignore[assignment]
    HAS_SWISSEPH = False


# ── Constants ─────────────────────────────────────────────────────────────
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Svati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

YOGAS = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva",
    "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan",
    "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla",
    "Brahma", "Indra", "Vaidhriti",
]

MOVABLE_KARANAS = [
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
]

WEEKDAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]

# Rahu Kalam period index (1-based, 1 to 8) from sunrise to sunset by weekday
RAHU_KALAM_PARTS = {
    "Monday": 2,
    "Saturday": 3,
    "Friday": 4,
    "Wednesday": 5,
    "Thursday": 6,
    "Tuesday": 7,
    "Sunday": 8,
}

# Day Choghadiya starting lord per weekday
CHOGHADIYA_ORDER = ["Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog"]

DAY_CHOGHADIYA_START = {
    "Sunday": "Udveg",
    "Monday": "Amrit",
    "Tuesday": "Rog",
    "Wednesday": "Labh",
    "Thursday": "Shubh",
    "Friday": "Char",
    "Saturday": "Kaal",
}

NIGHT_CHOGHADIYA_START = {
    "Sunday": "Shubh",
    "Monday": "Char",
    "Tuesday": "Kaal",
    "Wednesday": "Udveg",
    "Thursday": "Amrit",
    "Friday": "Rog",
    "Saturday": "Labh",
}

# Tithi names 1..15
TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",  # 15 in Krishna is Amavasya
]


@dataclass(frozen=True)
class PanchangSnapshot:
    dt_utc: datetime
    sun_sid_lon: float
    moon_sid_lon: float
    tithi_number: int  # 1 to 30
    tithi_name: str
    paksha: str  # "Shukla" | "Krishna"
    nakshatra_number: int  # 1 to 27
    nakshatra_name: str
    nakshatra_pada: int  # 1 to 4
    yoga_number: int  # 1 to 27
    yoga_name: str
    karana_name: str
    vara: str  # Weekday name
    sunrise_utc: datetime
    sunset_utc: datetime


@dataclass(frozen=True)
class TimeWindow:
    start_utc: datetime
    end_utc: datetime
    start_local: datetime
    end_local: datetime
    panchang: PanchangSnapshot
    choghadiya: str
    is_rahu_kalam: bool


# ── Julian Date & Astronomy Helpers ─────────────────────────────────────────

def datetime_to_jd(dt_utc: datetime) -> float:
    """Convert UTC datetime to Julian Day Number."""
    if dt_utc.tzinfo is not None:
        dt_utc = dt_utc.astimezone(timezone.utc)
    year = dt_utc.year
    month = dt_utc.month
    day = dt_utc.day + (dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0 + dt_utc.microsecond / 3.6e9) / 24.0

    if month <= 2:
        year -= 1
        month += 12

    A = int(year / 100)
    B = 2 - A + int(A / 4)
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5
    return jd


def jd_to_datetime(jd: float) -> datetime:
    """Convert Julian Day Number to UTC datetime."""
    jd += 0.5
    Z = int(jd)
    F = jd - Z
    if Z < 2299161:
        A = Z
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - int(alpha / 4)

    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)

    day = B - D - int(30.6001 * E) + F
    month = E - 1 if E < 14 else E - 13
    year = C - 4716 if month > 2 else C - 4715

    day_int = int(day)
    frac = day - day_int
    total_seconds = int(frac * 86400.0 + 0.5)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return datetime(year, month, day_int, hours, minutes, seconds, tzinfo=timezone.utc)


def _approx_lahiri_ayanamsa(jd: float) -> float:
    """Approximate Lahiri Ayanamsa for JD if swisseph is not installed."""
    # Ayanamsa on 2000-01-01 12:00 UT (JD 2451545.0) was ~23.858 degrees
    # Precession rate is ~50.29 arcseconds/year = ~0.013969 degrees/year
    t = (jd - 2451545.0) / 36525.0
    return 23.858 + 1.39697 * t


def _approx_sun_longitude(jd: float) -> float:
    """Approximate tropical Sun longitude in degrees (NOAA formula)."""
    t = (jd - 2451545.0) / 36525.0
    L0 = 280.46646 + 36000.76983 * t + 0.0003032 * (t ** 2)
    M = 357.52911 + 35999.05029 * t - 0.0001537 * (t ** 2)
    M_rad = math.radians(M % 360)
    C = (1.914602 - 0.004817 * t) * math.sin(M_rad) + (0.019993 - 0.000101 * t) * math.sin(2 * M_rad) + 0.000289 * math.sin(3 * M_rad)
    sun_true_lon = (L0 + C) % 360
    return sun_true_lon


def _approx_moon_longitude(jd: float) -> float:
    """Approximate tropical Moon longitude in degrees (Meeus truncated)."""
    t = (jd - 2451545.0) / 36525.0
    L_prime = 218.3164477 + 481267.88123421 * t
    D = 297.8501921 + 445267.1114034 * t
    M = 357.5291092 + 35999.0502909 * t
    M_prime = 134.9633964 + 477198.8675055 * t
    F = 93.2720950 + 483202.0175233 * t

    D_r = math.radians(D % 360)
    M_r = math.radians(M % 360)
    Mp_r = math.radians(M_prime % 360)
    F_r = math.radians(F % 360)

    # Main periodic terms in longitude
    sl = (
        6.288774 * math.sin(Mp_r)
        + 1.274027 * math.sin(2 * D_r - Mp_r)
        + 0.658314 * math.sin(2 * D_r)
        + 0.213618 * math.sin(2 * Mp_r)
        - 0.185116 * math.sin(M_r)
        - 0.114332 * math.sin(2 * F_r)
        + 0.058793 * math.sin(2 * D_r - 2 * Mp_r)
        + 0.057066 * math.sin(2 * D_r - M_r - Mp_r)
        + 0.053322 * math.sin(2 * D_r + Mp_r)
        + 0.045758 * math.sin(2 * D_r - M_r)
    )
    return (L_prime + sl) % 360


def _approx_sunrise_sunset(dt_utc: datetime, lat: float, lon: float) -> tuple[datetime, datetime]:
    """NOAA solar calculator approximation for sunrise and sunset."""
    # Day of year
    day_start = datetime(dt_utc.year, dt_utc.month, dt_utc.day, tzinfo=timezone.utc)
    N = (day_start - datetime(dt_utc.year, 1, 1, tzinfo=timezone.utc)).days + 1
    # approximate time
    lng_hour = lon / 15.0
    
    def calc_rise_or_set(is_rise: bool) -> datetime:
        t = N + ((6.0 - lng_hour) / 24.0) if is_rise else N + ((18.0 - lng_hour) / 24.0)
        M = (0.9856 * t) - 3.289
        M_r = math.radians(M % 360)
        L = M + (1.916 * math.sin(M_r)) + (0.020 * math.sin(2 * M_r)) + 282.634
        L = L % 360
        L_r = math.radians(L)
        
        RA = math.degrees(math.atan(0.91764 * math.tan(L_r))) % 360
        L_quad = (math.floor(L / 90.0)) * 90
        RA_quad = (math.floor(RA / 90.0)) * 90
        RA = (RA + (L_quad - RA_quad)) / 15.0

        sin_dec = 0.39782 * math.sin(L_r)
        cos_dec = math.cos(math.asin(sin_dec))
        
        zenith = 90.8333  # official standard zenith for sunrise/sunset
        zenith_r = math.radians(zenith)
        lat_r = math.radians(lat)
        
        cos_H = (math.cos(zenith_r) - (sin_dec * math.sin(lat_r))) / (cos_dec * math.cos(lat_r))
        cos_H = max(-1.0, min(1.0, cos_H))
        
        H = (360.0 - math.degrees(math.acos(cos_H))) if is_rise else math.degrees(math.acos(cos_H))
        H = H / 15.0
        
        T = H + RA - (0.06571 * t) - 6.622
        UT = (T - lng_hour) % 24.0
        
        hours = int(UT)
        minutes = int((UT - hours) * 60)
        seconds = int((((UT - hours) * 60) - minutes) * 60)
        return datetime(dt_utc.year, dt_utc.month, dt_utc.day, hours, minutes, seconds, tzinfo=timezone.utc)

    rise = calc_rise_or_set(is_rise=True)
    setting = calc_rise_or_set(is_rise=False)
    return rise, setting


def get_sun_moon_sidereal(dt_utc: datetime) -> tuple[float, float]:
    """Return sidereal (Sun longitude, Moon longitude) in degrees using Lahiri ayanamsa."""
    jd = datetime_to_jd(dt_utc)
    if HAS_SWISSEPH and swe is not None:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        sun_res = swe.calc_ut(jd, swe.SUN, flags)
        moon_res = swe.calc_ut(jd, swe.MOON, flags)
        sun_sid = sun_res[0][0] % 360
        moon_sid = moon_res[0][0] % 360
        return sun_sid, moon_sid
    else:
        ayanamsa = _approx_lahiri_ayanamsa(jd)
        sun_trop = _approx_sun_longitude(jd)
        moon_trop = _approx_moon_longitude(jd)
        sun_sid = (sun_trop - ayanamsa) % 360
        moon_sid = (moon_trop - ayanamsa) % 360
        return sun_sid, moon_sid


def get_sunrise_sunset(dt_utc: datetime, lat: float, lon: float) -> tuple[datetime, datetime]:
    """Compute sunrise and sunset UTC for given datetime and coordinates."""
    if HAS_SWISSEPH and swe is not None:
        jd_midnight = datetime_to_jd(datetime(dt_utc.year, dt_utc.month, dt_utc.day, 0, 0, tzinfo=timezone.utc))
        geopos = (lon, lat, 0.0)
        try:
            # Rise
            rise_res = swe.rise_trans(jd_midnight, swe.SUN, swe.CALC_RISE, geopos)
            set_res = swe.rise_trans(jd_midnight, swe.SUN, swe.CALC_SET, geopos)
            sunrise_utc = jd_to_datetime(rise_res[1][0])
            sunset_utc = jd_to_datetime(set_res[1][0])
            return sunrise_utc, sunset_utc
        except Exception:
            return _approx_sunrise_sunset(dt_utc, lat, lon)
    else:
        return _approx_sunrise_sunset(dt_utc, lat, lon)


# ── Core Panchang Calculation ────────────────────────────────────────────────

def get_panchang(dt: datetime, lat: float, lon: float) -> PanchangSnapshot:
    """Pure function calculating Vedic Panchang snapshot for given tz-aware datetime and coordinates."""
    dt_utc = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    sun_sid, moon_sid = get_sun_moon_sidereal(dt_utc)
    sunrise_utc, sunset_utc = get_sunrise_sunset(dt_utc, lat, lon)

    # Tithi: floor(((moon_lon - sun_lon) mod 360) / 12) + 1 (1 to 30)
    diff = (moon_sid - sun_sid) % 360
    tithi_number = int(math.floor(diff / 12.0)) + 1
    if tithi_number < 1:
        tithi_number = 1
    elif tithi_number > 30:
        tithi_number = 30

    if tithi_number <= 15:
        paksha = "Shukla"
        name_idx = tithi_number - 1
        tithi_name = TITHI_NAMES[name_idx]
    else:
        paksha = "Krishna"
        name_idx = tithi_number - 16
        if name_idx == 14:
            tithi_name = "Amavasya"
        else:
            tithi_name = TITHI_NAMES[name_idx]

    # Nakshatra: floor(moon_sidereal_lon / (360/27)), plus pada
    nakshatra_span = 360.0 / 27.0  # 13.3333333333 deg
    nak_idx = int(math.floor(moon_sid / nakshatra_span)) % 27
    nakshatra_number = nak_idx + 1
    nakshatra_name = NAKSHATRAS[nak_idx]

    pada_span = nakshatra_span / 4.0  # 3.3333333333 deg
    nakshatra_pada = int(math.floor((moon_sid % nakshatra_span) / pada_span)) + 1
    nakshatra_pada = min(max(nakshatra_pada, 1), 4)

    # Yoga: floor(((sun_sid + moon_sid) mod 360) / (360/27))
    yoga_idx = int(math.floor(((sun_sid + moon_sid) % 360) / nakshatra_span)) % 27
    yoga_number = yoga_idx + 1
    yoga_name = YOGAS[yoga_idx]

    # Karana: half-tithi, 1 to 60
    karana_idx = int(math.floor(diff / 6.0)) + 1
    if karana_idx == 1:
        karana_name = "Kimstughna"
    elif 2 <= karana_idx <= 57:
        karana_name = MOVABLE_KARANAS[(karana_idx - 2) % 7]
    elif karana_idx == 58:
        karana_name = "Shakuni"
    elif karana_idx == 59:
        karana_name = "Chatushpada"
    else:
        karana_name = "Naga"

    # Vara: weekday corresponding to the local solar day (from sunrise)
    # If before sunrise on that calendar date, traditional vara is previous day
    local_tz = dt.tzinfo or timezone.utc
    dt_local = dt_utc.astimezone(local_tz)
    sunrise_local = sunrise_utc.astimezone(local_tz)
    if dt_local < sunrise_local:
        effective_date = dt_local.date() - timedelta(days=1)
    else:
        effective_date = dt_local.date()
    vara = WEEKDAYS[effective_date.weekday()]

    return PanchangSnapshot(
        dt_utc=dt_utc,
        sun_sid_lon=round(sun_sid, 4),
        moon_sid_lon=round(moon_sid, 4),
        tithi_number=tithi_number,
        tithi_name=tithi_name,
        paksha=paksha,
        nakshatra_number=nakshatra_number,
        nakshatra_name=nakshatra_name,
        nakshatra_pada=nakshatra_pada,
        yoga_number=yoga_number,
        yoga_name=yoga_name,
        karana_name=karana_name,
        vara=vara,
        sunrise_utc=sunrise_utc,
        sunset_utc=sunset_utc,
    )


def compute_choghadiya(slot_mid_utc: datetime, sunrise_utc: datetime, sunset_utc: datetime, vara: str) -> str:
    """Compute the active Choghadiya name for a slot midpoint."""
    # Determine if day or night period
    if sunrise_utc <= slot_mid_utc < sunset_utc:
        # Day period: 8 equal parts
        day_duration = (sunset_utc - sunrise_utc).total_seconds()
        part_duration = day_duration / 8.0
        offset_seconds = (slot_mid_utc - sunrise_utc).total_seconds()
        part_idx = int(offset_seconds // part_duration)
        part_idx = min(max(part_idx, 0), 7)

        start_name = DAY_CHOGHADIYA_START.get(vara, "Udveg")
        start_idx = CHOGHADIYA_ORDER.index(start_name)
        active_idx = (start_idx + part_idx) % 7
        return CHOGHADIYA_ORDER[active_idx]
    else:
        # Night period: 8 equal parts
        # If before sunrise, night started on previous day's sunset
        start_name = NIGHT_CHOGHADIYA_START.get(vara, "Shubh")
        start_idx = CHOGHADIYA_ORDER.index(start_name)

        if slot_mid_utc >= sunset_utc:
            # First half of night
            # Next day sunrise approximation is sunset + 12h
            night_duration = 12 * 3600.0
            offset = (slot_mid_utc - sunset_utc).total_seconds()
        else:
            # Morning before sunrise
            night_duration = 12 * 3600.0
            offset = 12 * 3600.0 - (sunrise_utc - slot_mid_utc).total_seconds()

        part_idx = int(offset // (night_duration / 8.0)) if night_duration > 0 else 0
        part_idx = min(max(part_idx, 0), 7)
        active_idx = (start_idx + part_idx) % 7
        return CHOGHADIYA_ORDER[active_idx]


def is_in_rahu_kalam(slot_start_utc: datetime, slot_end_utc: datetime, sunrise_utc: datetime, sunset_utc: datetime, vara: str) -> bool:
    """Check if time slot overlaps with Rahu Kalam."""
    if slot_end_utc <= sunrise_utc or slot_start_utc >= sunset_utc:
        return False

    day_duration = (sunset_utc - sunrise_utc).total_seconds()
    part_duration = day_duration / 8.0
    part_idx = RAHU_KALAM_PARTS.get(vara, 8)  # 1 to 8

    rahu_start = sunrise_utc + timedelta(seconds=(part_idx - 1) * part_duration)
    rahu_end = sunrise_utc + timedelta(seconds=part_idx * part_duration)

    # Check interval overlap
    return max(slot_start_utc, rahu_start) < min(slot_end_utc, rahu_end)


@functools.lru_cache(maxsize=128)
def get_day_windows(day: dt_date, lat: float, lon: float, tz_str: str) -> tuple[TimeWindow, ...]:
    """Cut the day into 30-minute candidate slots, annotated with panchang, choghadiya, and Rahu Kalam.
    Cached in-memory per (date, lat, lon, tz).
    """
    user_tz = ZoneInfo(tz_str)
    # Start at 00:00 local time, end at 23:59:59 local time
    day_start_local = datetime.combine(day, time(0, 0), tzinfo=user_tz)
    
    # Precompute sunrise and sunset for the calendar date
    day_mid_utc = day_start_local.astimezone(timezone.utc) + timedelta(hours=12)
    sunrise_utc, sunset_utc = get_sunrise_sunset(day_mid_utc, lat, lon)

    windows: list[TimeWindow] = []
    # 48 slots of 30 minutes each
    for slot_i in range(48):
        slot_start_local = day_start_local + timedelta(minutes=slot_i * 30)
        slot_end_local = slot_start_local + timedelta(minutes=30)

        slot_start_utc = slot_start_local.astimezone(timezone.utc)
        slot_end_utc = slot_end_local.astimezone(timezone.utc)
        slot_mid_utc = slot_start_utc + timedelta(minutes=15)

        snap = get_panchang(slot_mid_utc, lat, lon)
        chog = compute_choghadiya(slot_mid_utc, sunrise_utc, sunset_utc, snap.vara)
        rahu = is_in_rahu_kalam(slot_start_utc, slot_end_utc, sunrise_utc, sunset_utc, snap.vara)

        windows.append(
            TimeWindow(
                start_utc=slot_start_utc,
                end_utc=slot_end_utc,
                start_local=slot_start_local,
                end_local=slot_end_local,
                panchang=snap,
                choghadiya=chog,
                is_rahu_kalam=rahu,
            )
        )

    return tuple(windows)
