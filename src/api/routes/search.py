from datetime import date
from fastapi import HTTPException

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.types.search_types import SearchRouteRequest
from src.core.database import get_db
from src.models.route import Route
from src.services.search_service import get_mapped_routes, get_routes_by_stops
from src.types.search_types import SearchRouteResponse

router = APIRouter(prefix="/search")


@router.post("/")
def search_route(search_request: SearchRouteRequest, db: Session = Depends(get_db)):
    print(f"🔍 Search request: from_stop_id={search_request.from_stop_id}, to_stop_id={search_request.to_stop_id}")

    # Default to today if no date provided
    search_date = search_request.date
    if not search_date:
        today = date.today()
        search_date = f"{today.year}-{today.month:02d}-{today.day:02d}"

    # for getting all routes from from_stop_id to to_stop_id
    route_ids = get_routes_by_stops(search_request.from_stop_id, search_request.to_stop_id, db)
    print(f"🔍 Found route_ids: {route_ids}")

    if not route_ids:
        raise HTTPException(
            status_code=404,
            detail="No routes found between the given stops."
        )

    # mapping stops in the routes (filtered by day if date provided)
    mapped_routes = get_mapped_routes(
        db, route_ids,
        search_request.from_stop_id, search_request.to_stop_id,
        date=search_date,
    )

    # Fetch route names
    route_names = {}
    if mapped_routes:
        ids = [r.route_id for r in mapped_routes]
        routes = db.execute(select(Route).where(Route.id.in_(ids))).scalars().all()
        for r in routes:
            route_names[r.id] = r.name

    # Attach route names
    for rm in mapped_routes:
        rm.route_name = route_names.get(rm.route_id, f"Route {rm.route_id}")

    print(f"🔍 Found route_ids: {mapped_routes}")
    return SearchRouteResponse(route_ids=mapped_routes)
