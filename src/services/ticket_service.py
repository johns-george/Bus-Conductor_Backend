from sqlalchemy.orm import Session
from src.models.ticket import Ticket
from src.utility.qr_utility import generate_qr_token
from datetime import datetime, timedelta

# Ticket validity: 4 hours from booking
TICKET_VALIDITY_HOURS = 4


def _expire_if_needed(db: Session, ticket: Ticket) -> Ticket:
    """Check if ticket has expired and update status accordingly."""
    if (
        ticket.expires_at is not None
        and ticket.status in ("PENDING_VALIDATION", "CONFIRMED", "ACTIVE")
        and datetime.utcnow() > ticket.expires_at
    ):
        ticket.status = "EXPIRED"
        db.commit()
        db.refresh(ticket)
    return ticket


def create_ticket(
    db: Session,
    user_id: int,
    trip_id: int,
    seat_id: int,
    source_stop_id: int,
    destination_stop_id: int,
    status: str = "PENDING_VALIDATION",
    price: float = 0.0,
    passenger_name: str | None = None,
    passenger_phone: str | None = None,
    passenger_count: int | None = None,
):
    now = datetime.utcnow()
    new_ticket = Ticket(
        user_id=user_id,
        trip_id=trip_id,
        source_stop_id=source_stop_id,
        destination_stop_id=destination_stop_id,
        booking_time=now,
        expires_at=now + timedelta(hours=TICKET_VALIDITY_HOURS),
        status=status,
        price=price,
        passenger_name=passenger_name,
        passenger_phone=passenger_phone,
        passenger_count=passenger_count or 1,
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    # Generate signed QR token for the ticket
    qr_token = generate_qr_token(ticket_id=new_ticket.id)
    new_ticket.qr_token = qr_token
    db.commit()
    db.refresh(new_ticket)

    return new_ticket


def get_all_tickets(db: Session, user_id: int):
    tickets = db.query(Ticket).filter(Ticket.user_id == user_id).order_by(Ticket.id.desc()).all()
    # Auto-expire tickets that have passed their expiry time
    for ticket in tickets:
        _expire_if_needed(db, ticket)
    return tickets


def get_ticket(db: Session, ticket_id: int):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket:
        _expire_if_needed(db, ticket)
    return ticket


def update_ticket(db: Session, ticket_id: int, ticket_data):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return {"error": "Ticket not found"}

    # Only allow editing of pending tickets (not yet validated or active)
    if ticket.status != "PENDING_VALIDATION":
        return {"error": f"Cannot edit ticket with status: {ticket.status}. Only pending tickets can be edited."}

    update_data = ticket_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ticket, key, value)
    db.commit()
    db.refresh(ticket)
    return ticket


def cancel_ticket(db: Session, ticket_id: int):
    """
    Cancel a ticket and refund to wallet if applicable.
    Returns a dict with ticket info + refund details.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return {"error": "Ticket not found", "refund": None}

    # Only allow cancellation of active/pending tickets
    if ticket.status not in ("PENDING_VALIDATION", "CONFIRMED", "ACTIVE"):
        return {
            "error": f"Cannot cancel ticket with status: {ticket.status}",
            "refund": None,
        }

    ticket.status = "CANCELLED"
    db.commit()
    db.refresh(ticket)

    # Attempt refund to wallet
    refund_amount = ticket.price
    refund_info = None

    if refund_amount > 0 and ticket.user_id:
        try:
            from src.dao.wallet_dao import get_or_create_wallet, top_up
            from src.dao.transaction_dao import create_transaction

            wallet = get_or_create_wallet(db, ticket.user_id)
            wallet = top_up(db, ticket.user_id, refund_amount)

            create_transaction(
                db,
                user_id=ticket.user_id,
                amount=refund_amount,
                type="REFUND",
                status="SUCCESSFUL",
                payment_method="WALLET",
                wallet_id=wallet.id,
                ticket_id=ticket.id,
                note=f"Refund for cancelled ticket #{ticket.id}",
                method_label="Wallet refund",
            )

            refund_info = {
                "amount": refund_amount,
                "wallet_balance": wallet.balance,
            }
        except Exception as e:
            # Refund failed but cancellation still went through
            refund_info = {"amount": refund_amount, "error": str(e)}

    return {
        "ticket_id": ticket.id,
        "status": ticket.status,
        "refund": refund_info,
    }
