from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.core.database import get_db
from src.services.stop_service import get_all_stops, search_stops

router = APIRouter(prefix="/stops")


def _stop_json(stop):
    return {
        "id": stop.id,
        "name": stop.name,
        "address": stop.address,
        "area": stop.area,
        "city": stop.city,
        "latitude": stop.latitude,
        "longitude": stop.longitude,
    }


@router.get("/get-all-stops")
def fetch_all_stops(
    db: Session = Depends(get_db),
    lat: Optional[float] = Query(None, description="User latitude for location-based sorting"),
    lng: Optional[float] = Query(None, description="User longitude for location-based sorting"),
    limit: int = Query(50, ge=1, le=100),
):
    stops = get_all_stops(db, lat=lat, lng=lng, limit=limit)
    return [_stop_json(s) for s in stops]


@router.get("/search")
def search_stops_endpoint(
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=2, description="Search query for stop names and addresses"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results to return"),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
):
    stops = search_stops(db, q, limit, lat=lat, lng=lng)
    return [_stop_json(s) for s in stops]