"""
Live weather via Open-Meteo (free, no API key required) for any location --
either a searched city name (geocoded first) or raw lat/lon (e.g. from the
browser's GPS). Powers both the public weather page and the dashboard's
day/night + sky-condition hero widget.
"""
import time
import urllib.request
import urllib.parse
import json

KARACHI_LAT = 24.8607
KARACHI_LON = 67.0011
KARACHI_LABEL = "Karachi, Pakistan"

# WMO weather codes -> a simplified condition bucket used for the sky graphic.
_CODE_MAP = {
    0: "clear", 1: "clear", 2: "cloudy", 3: "cloudy",
    45: "cloudy", 48: "cloudy",
    51: "rain", 53: "rain", 55: "rain", 56: "rain", 57: "rain",
    61: "rain", 63: "rain", 65: "rain", 66: "rain", 67: "rain",
    71: "rain", 73: "rain", 75: "rain", 77: "rain",
    80: "rain", 81: "rain", 82: "rain",
    85: "rain", 86: "rain",
    95: "storm", 96: "storm", 99: "storm",
}

_cache: dict[str, dict] = {}
_CACHE_TTL_SECONDS = 600


def _condition_label(code: int) -> str:
    bucket = _CODE_MAP.get(code, "cloudy")
    labels = {
        "clear": "Clear sky",
        "cloudy": "Cloudy",
        "rain": "Rain",
        "storm": "Thunderstorm",
    }
    return labels[bucket]


def _place_to_dict(place: dict) -> dict:
    parts = [place.get("name")]
    if place.get("admin1"):
        parts.append(place["admin1"])
    if place.get("country"):
        parts.append(place["country"])

    return {
        "label": ", ".join(p for p in parts if p),
        "lat": place["latitude"],
        "lon": place["longitude"],
    }


def search_cities(query: str, limit: int = 6) -> list[dict]:
    """Looks up a city name via Open-Meteo's free geocoding API and returns
    up to `limit` matches (for an autocomplete dropdown), each shaped like
    {"label", "lat", "lon"}. Empty list if nothing matches or the lookup
    fails."""
    query = query.strip()
    if not query:
        return []

    url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={urllib.parse.quote(query)}&count={limit}&language=en&format=json"
    )
    try:
        with urllib.request.urlopen(url, timeout=4) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        results = payload.get("results") or []
        return [_place_to_dict(place) for place in results]
    except Exception:
        return []


def geocode_city(query: str) -> dict | None:
    """Looks up a city name via Open-Meteo's free geocoding API.
    Returns {"label", "lat", "lon"} for the best match, or None if not found."""
    matches = search_cities(query, limit=1)
    return matches[0] if matches else None


def get_weather(lat: float = KARACHI_LAT, lon: float = KARACHI_LON, label: str = KARACHI_LABEL) -> dict:
    """Returns current weather for the given coordinates, cached per
    location for 10 minutes. Falls back to a safe default if unreachable."""
    cache_key = f"{round(lat, 2)},{round(lon, 2)}"
    now = time.time()
    cached = _cache.get(cache_key)
    if cached and (now - cached["fetched_at"]) < _CACHE_TTL_SECONDS:
        result = dict(cached["data"])
        result["location_label"] = label
        return result

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,is_day"
        "&timezone=auto"
    )

    try:
        with urllib.request.urlopen(url, timeout=4) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        current = payload["current"]
        code = current["weather_code"]
        bucket = _CODE_MAP.get(code, "cloudy")

        result = {
            "temperature_c": round(current["temperature_2m"], 1),
            "humidity_pct": current["relative_humidity_2m"],
            "wind_kmh": round(current["wind_speed_10m"], 1),
            "is_day": bool(current["is_day"]),
            "condition": bucket,
            "condition_label": _condition_label(code),
            "source": "live",
            "lat": lat,
            "lon": lon,
        }
    except Exception:
        result = {
            "temperature_c": None,
            "humidity_pct": None,
            "wind_kmh": None,
            "is_day": True,
            "condition": "cloudy",
            "condition_label": "Unavailable",
            "source": "fallback",
            "lat": lat,
            "lon": lon,
        }

    _cache[cache_key] = {"data": result, "fetched_at": now}
    result = dict(result)
    result["location_label"] = label
    return result


def get_karachi_weather() -> dict:
    """Back-compat helper: Karachi weather, used by the admin/analyst dashboard."""
    return get_weather(KARACHI_LAT, KARACHI_LON, KARACHI_LABEL)
