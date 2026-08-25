import math
from sqlalchemy.orm import Session
from src.models.stop import Stop


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in km using haversine formula."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_all_stops(db: Session, lat: float = None, lng: float = None, limit: int = 50):
    """Get all stops. If lat/lng provided, sort by distance. Otherwise alphabetical."""
    stops = db.query(Stop).all()

    if lat is not None and lng is not None:
        # Sort by distance from user's location
        stops_with_dist = []
        for s in stops:
            if s.latitude is not None and s.longitude is not None:
                dist = _haversine_km(lat, lng, s.latitude, s.longitude)
            else:
                dist = float("inf")
            stops_with_dist.append((dist, s))
        stops_with_dist.sort(key=lambda x: x[0])
        stops = [s for _, s in stops_with_dist]
    else:
        # Sort alphabetically by name
        stops.sort(key=lambda s: s.name.lower())

    return stops[:limit]


def search_stops(db: Session, query: str, limit: int = 20, lat: float = None, lng: float = None):
    """
    Search stops by name or address with fuzzy matching.
    If lat/lng provided, sort by distance. Otherwise by relevance.
    """
    if not query or len(query.strip()) < 2:
        return []

    query_str = query.strip().lower()

    stops = db.query(Stop).filter(
        (Stop.name.ilike(f"%{query_str}%")) |
        (Stop.address.ilike(f"%{query_str}%")) |
        (Stop.area.ilike(f"%{query_str}%")) |
        (Stop.city.ilike(f"%{query_str}%"))
    ).limit(limit * 2).all()  # fetch extra for sorting

    if lat is not None and lng is not None:
        stops_with_dist = []
        for s in stops:
            if s.latitude is not None and s.longitude is not None:
                dist = _haversine_km(lat, lng, s.latitude, s.longitude)
            else:
                dist = float("inf")
            stops_with_dist.append((dist, s))
        stops_with_dist.sort(key=lambda x: x[0])
        stops = [s for _, s in stops_with_dist]

    return stops[:limit]