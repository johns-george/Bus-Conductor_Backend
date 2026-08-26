import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.bus import Bus
from src.models.bus_route import BusRoute
from src.models.route import Route

logger = logging.getLogger("busconductor.bus")

router = APIRouter(prefix="/buses", tags=["buses"])


@router.get("/by-route/{route_id}")
def buses_by_route(route_id: int, db: Session = Depends(get_db)):
    try:
        logger.debug("Querying buses for route_id: %d", route_id)

        route_exists = db.query(Route).filter(Route.id == route_id).first()
        if not route_exists:
            logger.debug("Route %d not found", route_id)
            return {"route_id": route_id, "items": [], "message": "Route not found"}

        rows = db.query(BusRoute).filter(BusRoute.route_id == route_id).all()
        logger.debug("Found %d bus routes for route %d", len(rows), route_id)

        items = []
        for row in rows:
            try:
                items.append({
                    "id": row.bus.id,
                    "name": row.bus.name,
                    "bus_number": row.bus.bus_number,
                    "bus_type": row.bus.bus_type or "non_ac_seater",
                    "operator_name": row.bus.operator_name or "Default Operator",
                    "capacity": row.bus.capacity or 40,
                    "route_id": row.route_id,
                    "start_time": row.start_time.isoformat(),
                    "platform": row.platform or "P1",
                })
            except Exception as e:
                logger.warning("Error processing bus route %d: %s", row.id, e)
                continue

        logger.debug("Returning %d bus items", len(items))
        return {"route_id": route_id, "items": items, "message": "Buses by route"}

    except Exception as e:
        logger.error("Database error for route %d: %s", route_id, e)
        return {
            "route_id": route_id,
            "items": [],
            "message": f"Error retrieving buses: {str(e)}",
        }


@router.get("/{bus_id}")
def bus_detail(bus_id: int, db: Session = Depends(get_db)):
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if bus is None:
        raise HTTPException(status_code=404, detail="Bus not found")

    upcoming = [
        {
            "route_id": rel.route_id,
            "start_time": rel.start_time.isoformat(),
            "available_seats": rel.available_seats or 20,
            "platform": rel.platform or "P1",
        }
        for rel in bus.bus_routes
    ]
    return {
        "id": bus.id,
        "name": bus.name,
        "bus_number": bus.bus_number,
        "bus_type": bus.bus_type.value if bus.bus_type else "non_ac_seater",
        "operator_name": bus.operator_name or "Default Operator",
        "capacity": bus.capacity or 40,
        "upcoming_routes": upcoming,
        "message": "Bus detail",
    }


@router.get("/by-qr/{token}")
def bus_by_qr(token: str, db: Session = Depends(get_db)):
    bus_id_raw = token.removeprefix("bc:bus:")
    bus_id = int(bus_id_raw) if bus_id_raw.isdigit() else None
    if bus_id is None:
        raise HTTPException(status_code=400, detail="Invalid QR token")
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if bus is None:
        raise HTTPException(status_code=404, detail="Bus not found")
    return {
        "token": token,
        "bus": {
            "id": bus.id,
            "name": bus.name,
            "bus_number": bus.bus_number,
            "bus_type": bus.bus_type.value if bus.bus_type else "non_ac_seater",
            "operator_name": bus.operator_name or "Default Operator",
            "capacity": bus.capacity or 40,
        },
        "message": "Bus by QR",
    }
