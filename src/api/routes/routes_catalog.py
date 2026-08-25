from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.route import Route

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("/popular")
def popular_routes(limit: int = 6, db: Session = Depends(get_db)):
    rows = db.query(Route).order_by(Route.id.asc()).limit(limit).all()
    return {
        "items": [{"id": row.id, "name": row.name} for row in rows],
        "limit": limit,
        "message": "Popular routes",
    }


@router.get("/{route_id}")
def route_detail(route_id: int, db: Session = Depends(get_db)):
    route = db.query(Route).filter(Route.id == route_id).first()
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")

    ordered_stops = [
        {
            "id": rel.stop.id,
            "name": rel.stop.name,
            "address": rel.stop.address,
            "order": rel.stop_order,
        }
        for rel in route.route_stops
    ]

    return {
        "id": route.id,
        "name": route.name,
        "fare": 0,
        "distance_km": 0,
        "tags": [],
        "stops": ordered_stops,
        "message": "Route detail",
    }
