from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from src.core.database import get_db
from src.models.ticket import Ticket
from src.utility.qr_utility import validate_qr_token

router = APIRouter(prefix="/qr", tags=["qr"])


class QrValidateRequest(BaseModel):
    token: str


@router.post("/validate")
def validate_qr(payload: QrValidateRequest, db: Session = Depends(get_db)):
    """
    Validate a QR token.
    Returns ticket details if valid, error if invalid/expired/forged.
    """
    result = validate_qr_token(payload.token)

    if not result["valid"]:
        return {
            "valid": False,
            "expired": result["expired"],
            "message": result["message"],
            "ticket": None,
        }

    # Look up the ticket in the database
    ticket = db.query(Ticket).filter(Ticket.id == result["ticket_id"]).first()
    if ticket is None:
        return {
            "valid": False,
            "expired": False,
            "message": "Ticket not found in database",
            "ticket": None,
        }

    # Check ticket status
    if ticket.status == "CANCELLED":
        return {
            "valid": False,
            "expired": False,
            "message": "Ticket has been cancelled",
            "ticket": {
                "id": ticket.id,
                "status": ticket.status,
            },
        }

    if ticket.status == "VALIDATED":
        return {
            "valid": False,
            "expired": False,
            "message": "Ticket already used",
            "ticket": {
                "id": ticket.id,
                "status": ticket.status,
            },
        }

    # Mark ticket as validated
    ticket.status = "VALIDATED"
    db.commit()

    return {
        "valid": True,
        "expired": False,
        "message": "Ticket validated successfully",
        "ticket": {
            "id": ticket.id,
            "user_id": ticket.user_id,
            "trip_id": ticket.trip_id,
            "source_stop_id": ticket.source_stop_id,
            "destination_stop_id": ticket.destination_stop_id,
            "status": ticket.status,
            "price": ticket.price,
            "qr_token": ticket.qr_token,
        },
    }


@router.get("/info/{token}")
def qr_info(token: str, db: Session = Depends(get_db)):
    """
    Get ticket info from QR token without validating (for display purposes).
    """
    result = validate_qr_token(token)

    if not result["valid"]:
        return {
            "valid": False,
            "expired": result["expired"],
            "message": result["message"],
            "ticket": None,
        }

    ticket = db.query(Ticket).filter(Ticket.id == result["ticket_id"]).first()
    if ticket is None:
        return {
            "valid": False,
            "expired": False,
            "message": "Ticket not found",
            "ticket": None,
        }

    return {
        "valid": True,
        "expired": False,
        "message": "Ticket found",
        "ticket": {
            "id": ticket.id,
            "user_id": ticket.user_id,
            "trip_id": ticket.trip_id,
            "source_stop_id": ticket.source_stop_id,
            "destination_stop_id": ticket.destination_stop_id,
            "status": ticket.status,
            "price": ticket.price,
            "qr_token": ticket.qr_token,
        },
    }
