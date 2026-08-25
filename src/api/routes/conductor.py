from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.ticket import Ticket
from src.models.user import User
from src.utility.qr_utility import validate_qr_token

router = APIRouter(prefix="/conductor", tags=["conductor"])


class ConductorValidateRequest(BaseModel):
    token: str
    conductor_id: str  # Accepts username or numeric ID


class ConductorTicketIdRequest(BaseModel):
    ticket_id: int
    conductor_id: str


def _resolve_conductor(conductor_id: str, db: Session) -> User:
    """Look up conductor by numeric ID or username."""
    conductor = None
    try:
        conductor = db.query(User).filter(User.id == int(conductor_id)).first()
    except (ValueError, TypeError):
        pass
    if not conductor:
        conductor = db.query(User).filter(User.username == conductor_id).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor not found")
    if conductor.role != "CONDUCTOR":
        raise HTTPException(status_code=403, detail="Only conductors can validate tickets")
    return conductor


def _validate_and_mark(ticket_id: int, conductor: User, db: Session) -> dict:
    """Shared logic: find ticket, check status, mark validated."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket is None:
        return {"success": False, "message": "Ticket not found", "status": "NOT_FOUND"}

    if ticket.status == "VALIDATED":
        return {"success": False, "message": "Ticket already validated", "status": "ALREADY_VALIDATED", "ticket": _ticket_info(ticket)}
    if ticket.status == "CANCELLED":
        return {"success": False, "message": "Ticket has been cancelled", "status": "CANCELLED", "ticket": _ticket_info(ticket)}
    if ticket.status == "EXPIRED":
        return {"success": False, "message": "Ticket has expired", "status": "EXPIRED", "ticket": _ticket_info(ticket)}

    ticket.status = "VALIDATED"
    from datetime import datetime
    ticket.validated_at = datetime.utcnow()
    ticket.validated_by = conductor.id
    db.commit()

    passenger = db.query(User).filter(User.id == ticket.user_id).first()
    return {
        "success": True,
        "message": "Ticket validated successfully",
        "status": "VALIDATED",
        "validated_by": conductor.full_name or conductor.username,
        "ticket": _ticket_info(ticket),
        "passenger": {
            "name": passenger.full_name if passenger else "Unknown",
            "id": passenger.id if passenger else None,
        } if passenger else None,
    }


@router.post("/validate")
def conductor_validate_ticket(payload: ConductorValidateRequest, db: Session = Depends(get_db)):
    """Conductor validates a passenger's QR ticket."""
    conductor = _resolve_conductor(payload.conductor_id, db)

    result = validate_qr_token(payload.token)
    if not result.get("valid"):
        return {"success": False, "message": result.get("error", "Invalid QR token"), "status": "INVALID"}

    ticket_id = result.get("ticket_id")
    if ticket_id is None:
        return {"success": False, "message": "No ticket ID in QR token", "status": "INVALID"}

    return _validate_and_mark(ticket_id, conductor, db)


@router.post("/validate-by-id")
def conductor_validate_by_ticket_id(payload: ConductorTicketIdRequest, db: Session = Depends(get_db)):
    """Conductor validates a ticket by entering the ticket ID directly."""
    conductor = _resolve_conductor(payload.conductor_id, db)
    return _validate_and_mark(payload.ticket_id, conductor, db)


@router.get("/validated-tickets/{conductor_id}")
def get_validated_tickets(conductor_id: str, db: Session = Depends(get_db)):
    """Get all tickets validated by this conductor."""
    # Resolve conductor
    conductor = None
    try:
        conductor = db.query(User).filter(User.id == int(conductor_id)).first()
    except (ValueError, TypeError):
        pass
    if not conductor:
        conductor = db.query(User).filter(User.username == conductor_id).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor not found")

    tickets = (
        db.query(Ticket)
        .filter(Ticket.validated_by == conductor.id)
        .order_by(Ticket.validated_at.desc())
        .all()
    )

    results = []
    for t in tickets:
        passenger = db.query(User).filter(User.id == t.user_id).first()
        results.append({
            **_ticket_info(t),
            "validated_at": t.validated_at.isoformat() if t.validated_at else None,
            "passenger_name": passenger.full_name if passenger else "Unknown",
            "passenger_email": passenger.email if passenger else None,
        })

    return results


def _ticket_info(ticket):
    return {
        "id": ticket.id,
        "trip_id": ticket.trip_id,
        "status": ticket.status,
        "price": ticket.price,
        "source_stop_id": ticket.source_stop_id,
        "destination_stop_id": ticket.destination_stop_id,
        "booking_time": ticket.booking_time.isoformat() if ticket.booking_time else None,
        "expires_at": ticket.expires_at.isoformat() if ticket.expires_at else None,
    }
