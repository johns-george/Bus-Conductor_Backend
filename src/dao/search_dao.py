from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, distinct
from src.models.route import Route
from src.models.route_stop import RouteStop
from src.models.stop import Stop
from src.models.edge import Edge
from src.models.bus_route import BusRoute
from src.models.bus import Bus

# returns route ids that have both from_stop_id and to_stop_id in the traveling order
def fetch_routes_by_stops(
    db: Session,
    from_stop_id: int,
    to_stop_id: int
):
    print(f"🔍 DAO: Searching for routes from stop {from_stop_id} to stop {to_stop_id}")
    
    # Find routes that contain both stops in correct order
    from_rs = aliased(RouteStop)
    to_rs = aliased(RouteStop)
    
    query = (
        select(from_rs.route_id)
        .join(to_rs, from_rs.route_id == to_rs.route_id)
        .where(
            from_rs.stop_id == from_stop_id,
            to_rs.stop_id == to_stop_id,
            from_rs.stop_order < to_rs.stop_order  # Ensure correct traveling order
        )
        .distinct()
    )
    
    print(f"🔍 DAO: Query: {query}")
    result = db.execute(query).scalars().all()
    print(f"🔍 DAO: Found route IDs: {result}")
    return result

# get buses for given route ids
def fetch_buses_by_routes(
    db: Session,
    route_ids: list[int]
):
    print(f"🔍 DAO: Finding buses for route IDs: {route_ids}")
    
    query = (
        select(
            Bus.id,
            Bus.name,
            Bus.bus_number,
            BusRoute.route_id,
            BusRoute.start_time
        )
        .join(BusRoute, Bus.id == BusRoute.bus_id)
        .where(BusRoute.route_id.in_(route_ids))
        .order_by(BusRoute.start_time)
    )
    
    print(f"🔍 DAO: Bus query: {query}")
    result = db.execute(query).all()
    print(f"🔍 DAO: Found {len(result)} buses")
    return result

# main search function - takes stop names and returns buses
def search_buses_by_stop_names(
    db: Session,
    from_stop_name: str,
    to_stop_name: str
):
    print(f"🔍 DAO: Searching buses from '{from_stop_name}' to '{to_stop_name}'")
    
    # Get stop IDs from names
    from_stop = db.execute(
        select(Stop.id).where(Stop.name == from_stop_name)
    ).scalar_one_or_none()
    
    to_stop = db.execute(
        select(Stop.id).where(Stop.name == to_stop_name)
    ).scalar_one_or_none()
    
    if not from_stop:
        print(f"🔍 DAO: From stop '{from_stop_name}' not found")
        return []
    if not to_stop:
        print(f"🔍 DAO: To stop '{to_stop_name}' not found")
        return []
    
    # Find routes containing both stops
    route_ids = fetch_routes_by_stops(db, from_stop, to_stop)
    
    if not route_ids:
        print(f"🔍 DAO: No routes found between stops")
        return []
    
    # Get buses for those routes
    buses = fetch_buses_by_routes(db, route_ids)
    return buses

# return bus schedules for given route ids
def fetch_buses_schedule_by_routes(
    db: Session,
    route_ids: list[int],
    day_abbr: str | None = None,
):
    """Return all bus schedules for the given routes, ordered by start_time.
    If day_abbr is provided, only return buses that run on that day."""
    query = (
        select(
            BusRoute.route_id,
            Bus.id.label("bus_id"),
            Bus.name.label("bus_name"),
            Bus.bus_number,
            Bus.bus_type,
            Bus.operator_name,
            Bus.capacity,
            BusRoute.start_time,
            BusRoute.platform,
            BusRoute.days_of_week,
        )
        .join(Bus, Bus.id == BusRoute.bus_id)
        .where(BusRoute.route_id.in_(route_ids))
        .order_by(BusRoute.start_time)
    )
    rows = db.execute(query).all()
    if day_abbr:
        rows = [
            r for r in rows
            if not r.days_of_week
            or day_abbr.lower() in [d.strip().lower() for d in r.days_of_week.split(",")]
        ]
    return rows


# return the ordered stops in a route
def fetch_route_stops_by_route_id(
    db: Session,
    route_id: int,
    from_stop_id: int,
    to_stop_id: int
):
    """
    DAO function that returns ordered stop names and
    distances between consecutive stops for a given route.
    """

    # Get the route with its stops
    route = db.execute(
        select(Route).where(Route.id == route_id)
    ).scalar_one()

    # Get all route stops for this route in order
    route_stops = db.execute(
        select(RouteStop)
        .where(RouteStop.route_id == route_id)
        .order_by(RouteStop.stop_order)
    ).scalars().all()

    # Get stop information with distances
    rs = aliased(RouteStop)
    rs_next = aliased(RouteStop)
    
    query = (
        select(
            rs.stop_id,
            Stop.name.label("stop_name"),
            rs.stop_order,
            Edge.distance.label("distance")
        )
        .join(Stop, Stop.id == rs.stop_id)
        .outerjoin(
            rs_next,
            (rs.route_id == rs_next.route_id) &
            (rs_next.stop_order == rs.stop_order + 1)
        )
        .outerjoin(
            Edge,
            (Edge.from_stop == rs.stop_id) &
            (Edge.to_stop == rs_next.stop_id)
        )
        .where(
            rs.route_id == route_id
        )
        .order_by(rs.stop_order)
    )
    print(f"🔍 DAO: Query: {query}")
    # Return raw rows for the service layer to map
    return db.execute(query).all()