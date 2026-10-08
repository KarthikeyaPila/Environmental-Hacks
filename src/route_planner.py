"""Privacy-safe route previews for kabadiwala pickup opportunities."""

from math import atan2, cos, radians, sin, sqrt


def plan_preview(origin: dict, stops: list[dict]) -> dict:
    """Order approximate stops with a nearest-neighbour preview algorithm."""
    remaining = list(stops)
    ordered = []
    current = origin
    total_km = 0.0
    while remaining:
        next_stop = min(remaining, key=lambda stop: _distance(current, stop))
        total_km += _distance(current, next_stop)
        ordered.append({**next_stop, "stopNumber": len(ordered) + 1})
        current = next_stop
        remaining.remove(next_stop)
    total_km += _distance(current, origin) if ordered else 0
    return {
        "mode": "local-preview",
        "optimizeFor": "distance",
        "origin": origin,
        "stops": ordered,
        "route": [origin, *ordered, origin] if ordered else [origin],
        "totalDistanceKm": round(total_km, 2),
        "estimatedDurationMinutes": round(total_km * 4),
        "privacy": "approximate coordinates; no household addresses",
    }


def _distance(a: dict, b: dict) -> float:
    lat1, lon1, lat2, lon2 = map(radians, (a["latitude"], a["longitude"], b["latitude"], b["longitude"]))
    haversine = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * atan2(sqrt(haversine), sqrt(1 - haversine))
