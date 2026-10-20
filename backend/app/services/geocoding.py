"""Geocoding service using Open-Meteo Geocoding API with robust fallbacks."""

from __future__ import annotations

import httpx
import structlog

logger = structlog.get_logger(__name__)

# Fallback coordinates for common locations
KNOWN_LOCATIONS = {
    "bengaluru": (12.9716, 77.5946, "Asia/Kolkata"),
    "bangalore": (12.9716, 77.5946, "Asia/Kolkata"),
    "delhi": (28.6139, 77.2090, "Asia/Kolkata"),
    "new delhi": (28.6139, 77.2090, "Asia/Kolkata"),
    "mumbai": (19.0760, 72.8777, "Asia/Kolkata"),
    "chennai": (13.0827, 80.2707, "Asia/Kolkata"),
    "kolkata": (22.5726, 88.3639, "Asia/Kolkata"),
    "hyderabad": (17.3850, 78.4867, "Asia/Kolkata"),
    "pune": (18.5204, 73.8567, "Asia/Kolkata"),
    "london": (51.5074, -0.1278, "Europe/London"),
    "new york": (40.7128, -74.0060, "America/New_York"),
    "san francisco": (37.7749, -122.4194, "America/Los_Angeles"),
}

DEFAULT_FALLBACK = (12.9716, 77.5946, "Asia/Kolkata")


async def geocode_location(location_name: str | None, default_city: str | None = None) -> tuple[float, float, str]:
    """Resolve location_name to (latitude, longitude, timezone).
    Calls Open-Meteo geocoding API, falls back to default_city or Bengaluru.
    """
    target = (location_name or default_city or "Bengaluru").strip()
    target_lower = target.lower()

    if target_lower in KNOWN_LOCATIONS:
        return KNOWN_LOCATIONS[target_lower]

    # Try Open-Meteo Geocoding API
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={target}&count=1&language=en&format=json"
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results")
                if results and len(results) > 0:
                    first = results[0]
                    lat = float(first["latitude"])
                    lon = float(first["longitude"])
                    tz = first.get("timezone", "Asia/Kolkata")
                    return lat, lon, tz
    except Exception as exc:
        logger.warning("Geocoding failed, using fallback", location=target, error=str(exc))

    return DEFAULT_FALLBACK
