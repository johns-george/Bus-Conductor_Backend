from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.services.ticket_service import get_all_tickets, get_ticket, create_ticket, update_ticket, cancel_ticket
from src.schemas.ticket_response import TicketResponse
from src.models.ticket import TicketUpdate
from typing import List

router = APIRouter(prefix="/tickets")


@router.post("/book-ticket")
def book_ticket(
    user_id: int,
    trip_id: int,
    seat_id: int,
    source_stop_id: int,
    destination_stop_id: int,
    price: float = 0.0,
    db: Session = Depends(get_db),
):
    return create_ticket(
        db,
        user_id,
        trip_id,
        seat_id,
        source_stop_id,
        destination_stop_id,
        price=price,
    )


@router.get("/get-all-tickets/{user_id}", response_model=List[TicketResponse])
def fetch_all_tickets(user_id: int, db: Session = Depends(get_db)):
    return get_all_tickets(db, user_id)


@router.get("/get-ticket-details/{ticket_id}", response_model=TicketResponse)
def fetch_ticket(ticket_id: int, db: Session = Depends(get_db)):
    return get_ticket(db, ticket_id)


@router.put("/update-ticket/{ticket_id}")
def update_ticket_details(
    ticket_id: int, ticket_data: TicketUpdate, db: Session = Depends(get_db)
):
    return update_ticket(db, ticket_id, ticket_data)


@router.post("/cancel-ticket/{ticket_id}")
def cancel(ticket_id: int, db: Session = Depends(get_db)):
    result = cancel_ticket(db, ticket_id)
    if "error" in result and result["error"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
