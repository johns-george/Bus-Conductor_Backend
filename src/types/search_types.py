from typing import Optional
from pydantic import BaseModel


class SearchRouteRequest(BaseModel):
    from_stop_id: int
    to_stop_id: int
    date: Optional[str] = None  # ISO date string e.g. "2026-08-25"


class WeightedStopMap(BaseModel):
    stop_name: str
    distance: float


class BusInfo(BaseModel):
    bus_id: int
    bus_name: Optional[str] = None
    bus_number: Optional[str] = None
    bus_type: Optional[str] = None
    operator_name: Optional[str] = None
    capacity: int = 0
    start_time: str  # ISO format time string e.g. "08:30:00"
    platform: str = "P1"
    days_of_week: Optional[str] = None


class RouteMap(BaseModel):
    route_id: int
    route_name: Optional[str] = None
    total_distance: float
    estimated_fare: int
    estimated_travel_minutes: int
    stops: list[WeightedStopMap]
    buses: list[BusInfo] = []
    next_departure: Optional[str] = None  # ISO format time of next bus
    total_buses_on_date: int = 0


class SearchRouteResponse(BaseModel):
    route_ids: list[RouteMap]
