"""Geocoding service using Open-Meteo Geocoding API with robust fallbacks."""

from __future__ import annotations

import httpx
import structlog

logger = structlog.get_logger(__name__)

# Fallback coordinates for common locations across India and international diaspora
KNOWN_LOCATIONS = {
    # Metros & Major Hubs
    "bengaluru": (12.9716, 77.5946, "Asia/Kolkata"),
    "bangalore": (12.9716, 77.5946, "Asia/Kolkata"),
    "delhi": (28.6139, 77.2090, "Asia/Kolkata"),
    "new delhi": (28.6139, 77.2090, "Asia/Kolkata"),
    "mumbai": (19.0760, 72.8777, "Asia/Kolkata"),
    "chennai": (13.0827, 80.2707, "Asia/Kolkata"),
    "kolkata": (22.5726, 88.3639, "Asia/Kolkata"),
    "hyderabad": (17.3850, 78.4867, "Asia/Kolkata"),
    "pune": (18.5204, 73.8567, "Asia/Kolkata"),
    "ahmedabad": (23.0225, 72.5714, "Asia/Kolkata"),
    # North India
    "chandigarh": (30.7333, 76.7794, "Asia/Kolkata"),
    "jaipur": (26.9124, 75.7873, "Asia/Kolkata"),
    "jodhpur": (26.2389, 73.0243, "Asia/Kolkata"),
    "udaipur": (24.5854, 73.7125, "Asia/Kolkata"),
    "lucknow": (26.8467, 80.9462, "Asia/Kolkata"),
    "kanpur": (26.4499, 80.3319, "Asia/Kolkata"),
    "varanasi": (25.3176, 82.9739, "Asia/Kolkata"),
    "kashi": (25.3176, 82.9739, "Asia/Kolkata"),
    "prayagraj": (25.4358, 81.8463, "Asia/Kolkata"),
    "allahabad": (25.4358, 81.8463, "Asia/Kolkata"),
    "ayodhya": (26.7922, 82.1998, "Asia/Kolkata"),
    "agra": (27.1767, 78.0081, "Asia/Kolkata"),
    "mathura": (27.4924, 77.6737, "Asia/Kolkata"),
    "vrindavan": (27.5806, 77.7006, "Asia/Kolkata"),
    "haridwar": (29.9457, 78.1642, "Asia/Kolkata"),
    "rishikesh": (30.0869, 78.2676, "Asia/Kolkata"),
    "dehradun": (30.3165, 78.0322, "Asia/Kolkata"),
    "amritsar": (31.6340, 74.8723, "Asia/Kolkata"),
    "ludhiana": (30.9010, 75.8573, "Asia/Kolkata"),
    "noida": (28.5355, 77.3910, "Asia/Kolkata"),
    "gurugram": (28.4595, 77.0266, "Asia/Kolkata"),
    "gurgaon": (28.4595, 77.0266, "Asia/Kolkata"),
    "jammu": (32.7266, 74.8570, "Asia/Kolkata"),
    "srinagar": (34.0837, 74.7973, "Asia/Kolkata"),
    "shimla": (31.1048, 77.1734, "Asia/Kolkata"),
    # West & Central India
    "surat": (21.1702, 72.8311, "Asia/Kolkata"),
    "vadodara": (22.3072, 73.1812, "Asia/Kolkata"),
    "baroda": (22.3072, 73.1812, "Asia/Kolkata"),
    "rajkot": (22.3039, 70.8022, "Asia/Kolkata"),
    "gandhinagar": (23.2156, 72.6369, "Asia/Kolkata"),
    "nagpur": (21.1458, 79.0882, "Asia/Kolkata"),
    "nashik": (19.9975, 73.7898, "Asia/Kolkata"),
    "thane": (19.2183, 72.9781, "Asia/Kolkata"),
    "navi mumbai": (19.0330, 73.0297, "Asia/Kolkata"),
    "aurangabad": (19.8762, 75.3433, "Asia/Kolkata"),
    "chhatrapati sambhajinagar": (19.8762, 75.3433, "Asia/Kolkata"),
    "indore": (22.7196, 75.8577, "Asia/Kolkata"),
    "bhopal": (23.2599, 77.4126, "Asia/Kolkata"),
    "ujjain": (23.1765, 75.7885, "Asia/Kolkata"),
    "gwalior": (26.2183, 78.1828, "Asia/Kolkata"),
    "jabalpur": (23.1815, 79.9864, "Asia/Kolkata"),
    "raipur": (21.2514, 81.6296, "Asia/Kolkata"),
    "goa": (15.4909, 73.8278, "Asia/Kolkata"),
    "panaji": (15.4909, 73.8278, "Asia/Kolkata"),
    # South India
    "kochi": (9.9312, 76.2673, "Asia/Kolkata"),
    "cochin": (9.9312, 76.2673, "Asia/Kolkata"),
    "thiruvananthapuram": (8.5241, 76.9366, "Asia/Kolkata"),
    "trivandrum": (8.5241, 76.9366, "Asia/Kolkata"),
    "kozhikode": (11.2588, 75.7804, "Asia/Kolkata"),
    "calicut": (11.2588, 75.7804, "Asia/Kolkata"),
    "visakhapatnam": (17.6868, 83.2185, "Asia/Kolkata"),
    "vizag": (17.6868, 83.2185, "Asia/Kolkata"),
    "vijayawada": (16.5062, 80.6480, "Asia/Kolkata"),
    "tirupati": (13.6288, 79.4192, "Asia/Kolkata"),
    "warangal": (17.9689, 79.5941, "Asia/Kolkata"),
    "coimbatore": (11.0168, 76.9558, "Asia/Kolkata"),
    "madurai": (9.9252, 78.1198, "Asia/Kolkata"),
    "trichy": (10.7905, 78.7047, "Asia/Kolkata"),
    "tiruchirappalli": (10.7905, 78.7047, "Asia/Kolkata"),
    "salem": (11.6643, 78.1460, "Asia/Kolkata"),
    "mysuru": (12.2958, 76.6394, "Asia/Kolkata"),
    "mysore": (12.2958, 76.6394, "Asia/Kolkata"),
    "mangaluru": (12.9141, 74.8560, "Asia/Kolkata"),
    "mangalore": (12.9141, 74.8560, "Asia/Kolkata"),
    "hubballi": (15.3647, 75.1240, "Asia/Kolkata"),
    "hubli": (15.3647, 75.1240, "Asia/Kolkata"),
    "belagavi": (15.8497, 74.4977, "Asia/Kolkata"),
    "belgaum": (15.8497, 74.4977, "Asia/Kolkata"),
    # East & North-East India
    "patna": (25.5941, 85.1376, "Asia/Kolkata"),
    "gaya": (24.7914, 85.0002, "Asia/Kolkata"),
    "ranchi": (23.3441, 85.3096, "Asia/Kolkata"),
    "jamshedpur": (22.8046, 86.2029, "Asia/Kolkata"),
    "bhubaneswar": (20.2961, 85.8245, "Asia/Kolkata"),
    "cuttack": (20.4625, 85.8828, "Asia/Kolkata"),
    "puri": (19.8135, 85.8312, "Asia/Kolkata"),
    "guwahati": (26.1445, 91.7362, "Asia/Kolkata"),
    "shillong": (25.5788, 91.8933, "Asia/Kolkata"),
    "siliguri": (26.7271, 88.3953, "Asia/Kolkata"),
    "agartala": (23.8315, 91.2868, "Asia/Kolkata"),
    "imphal": (24.8170, 93.9368, "Asia/Kolkata"),
    # International Diaspora
    "dubai": (25.2048, 55.2708, "Asia/Dubai"),
    "singapore": (1.3521, 103.8198, "Asia/Singapore"),
    "london": (51.5074, -0.1278, "Europe/London"),
    "new york": (40.7128, -74.0060, "America/New_York"),
    "san francisco": (37.7749, -122.4194, "America/Los_Angeles"),
    "toronto": (43.6532, -79.3832, "America/Toronto"),
    "sydney": (-33.8688, 151.2093, "Australia/Sydney"),
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
