from typing import List
from datetime import datetime, time
from sqlalchemy.orm import Session

from src.dao.search_dao import (
    fetch_routes_by_stops,
    fetch_route_stops_by_route_id,
    fetch_buses_schedule_by_routes,
)

from src.types.search_types import (
    RouteMap,
    WeightedStopMap,
    BusInfo,
)


def get_routes_by_stops(
    from_stop_id: int,
    to_stop_id: int,
    db: Session
):
    return fetch_routes_by_stops(
        db=db,
        from_stop_id=from_stop_id,
        to_stop_id=to_stop_id,
    )


def _time_to_iso(t) -> str:
    """Convert a DB time object to ISO format string."""
    if t is None:
        return "00:00:00"
    if isinstance(t, time):
        return t.strftime("%H:%M:%S")
    return str(t)


_DAY_ABBRS = {
    0: "mon", 1: "tue", 2: "wed", 3: "thu",
    4: "fri", 5: "sat", 6: "sun",
}


def _date_to_day_abbr(date_str: str | None) -> str | None:
    """Convert ISO date string (YYYY-MM-DD) to day abbreviation."""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return _DAY_ABBRS.get(dt.weekday())
    except (ValueError, TypeError):
        return None


def get_mapped_routes(
    db: Session,
    route_ids: List[int],
    from_stop_id: int,
    to_stop_id: int,
    date: str | None = None,
) -> List[RouteMap]:

    mapped_routes: List[RouteMap] = []
    day_abbr = _date_to_day_abbr(date)

    # Fetch bus schedules for all matched routes, filtered by day
    all_bus_schedules = fetch_buses_schedule_by_routes(db, route_ids, day_abbr=day_abbr)

    # Group schedules by route_id
    schedules_by_route = {}
    for row in all_bus_schedules:
        rid = row.route_id
        if rid not in schedules_by_route:
            schedules_by_route[rid] = []
        schedules_by_route[rid].append(row)

    for route_id in route_ids:

        # Skip routes that have no buses running on the selected day
        if day_abbr and not schedules_by_route.get(route_id):
            continue

        rows = fetch_route_stops_by_route_id(
            db=db,
            route_id=route_id,
            from_stop_id=from_stop_id,
            to_stop_id=to_stop_id,
        )

        if not rows:
            continue

        filtered_rows = []
        collecting = False
        seen_stop_orders = set()

        for row in rows:
            if row.stop_id == from_stop_id:
                collecting = True

            if collecting:
                if row.stop_order not in seen_stop_orders:
                    filtered_rows.append(row)
                    seen_stop_orders.add(row.stop_order)

            if row.stop_id == to_stop_id and collecting:
                break

        # Must contain source and destination
        if len(filtered_rows) < 2:
            continue

        stops: List[WeightedStopMap] = []
        total_distance = 0.0

        for row in filtered_rows:
            distance = (
                round(float(row.distance), 2)
                if row.distance
                else 0.0
            )
            total_distance += distance
            stops.append(
                WeightedStopMap(
                    stop_name=row.stop_name,
                    distance=distance,
                )
            )

        # Use actual total distance from edge data for fare calculation
        estimated_fare = max(10, round(total_distance * 2.2))
        estimated_travel_minutes = round(total_distance * 3)

        # Build bus info from real schedules
        route_schedules = schedules_by_route.get(route_id, [])
        buses: List[BusInfo] = []
        now = datetime.now()
        now_time = now.time()

        next_departure = None

        for sched in route_schedules:
            bus = BusInfo(
                bus_id=sched.bus_id,
                bus_name=sched.bus_name,
                bus_number=sched.bus_number,
                bus_type=sched.bus_type,
                operator_name=sched.operator_name,
                capacity=sched.capacity or 0,
                start_time=_time_to_iso(sched.start_time),
                platform=sched.platform or "P1",
            )
            buses.append(bus)

            # Find next departure (first bus after now)
            if next_departure is None and sched.start_time:
                if sched.start_time >= now_time:
                    next_departure = _time_to_iso(sched.start_time)

        # If all buses have departed today, show first one as next
        if next_departure is None and buses:
            next_departure = buses[0].start_time

        route_map = RouteMap(
            route_id=route_id,
            total_distance=round(total_distance, 2),
            estimated_fare=estimated_fare,
            estimated_travel_minutes=estimated_travel_minutes,
            stops=stops,
            buses=buses,
            next_departure=next_departure,
            total_buses_on_date=len(buses),
        )

        mapped_routes.append(route_map)

    return mapped_routes
