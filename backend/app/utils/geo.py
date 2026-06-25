"""
ResQNet AI - Geospatial Utilities
Distance calculations, nearest-resource queries, and coordinate helpers.
"""

import math
from typing import List, Tuple, Optional


EARTH_RADIUS_KM = 6371.0


def haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula. Returns distance in kilometers.
    """
    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def estimate_travel_time_minutes(
    distance_km: float,
    speed_kmh: float = 40.0,
) -> float:
    """
    Estimate travel time in minutes given distance and average speed.
    Default speed accounts for emergency conditions (40 km/h).
    """
    if speed_kmh <= 0:
        return float("inf")
    return (distance_km / speed_kmh) * 60


def find_nearest(
    target_lat: float,
    target_lon: float,
    candidates: List[dict],
    top_n: int = 5,
) -> List[Tuple[dict, float]]:
    """
    Find the nearest candidates to a target location.
    Each candidate dict must have 'location.coordinates' as [lon, lat].
    Returns list of (candidate, distance_km) sorted by distance.
    """
    results = []
    for candidate in candidates:
        try:
            coords = candidate.get("location", {}).get("coordinates", [])
            if len(coords) >= 2:
                dist = haversine_distance(target_lat, target_lon, coords[1], coords[0])
                results.append((candidate, dist))
        except (TypeError, IndexError):
            continue

    results.sort(key=lambda x: x[1])
    return results[:top_n]


def geojson_point(longitude: float, latitude: float) -> dict:
    """Create a GeoJSON Point."""
    return {
        "type": "Point",
        "coordinates": [longitude, latitude],
    }


def extract_coords(location: dict) -> Optional[Tuple[float, float]]:
    """Extract (latitude, longitude) from a GeoJSON Point location dict."""
    try:
        coords = location.get("coordinates", [])
        if len(coords) >= 2:
            return (coords[1], coords[0])  # (lat, lon)
    except (TypeError, AttributeError):
        pass
    return None
