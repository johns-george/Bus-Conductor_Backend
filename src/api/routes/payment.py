import time
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.services.ticket_service import create_ticket
from src.dao.wallet_dao import get_or_create_wallet, debit as wallet_debit
from src.dao.transaction_dao import create_transaction

router = APIRouter(prefix="/payments", tags=["payments"])


class ProcessPaymentRequest(BaseModel):
    user_id: int
    amount: float
    method_id: str
    method_type: str
    booking_id: str
    note: str | None = None
    method_label: str | None = None
    trip_id: int | None = None
    seat_id: int | None = None
    source_stop_id: int | None = None
    destination_stop_id: int | None = None
    passenger_name: str | None = None
    passenger_phone: str | None = None
    passenger_count: int | None = None


@router.post("/process")
def process_payment(payload: ProcessPaymentRequest, db: Session = Depends(get_db)):
    print(f"💳 Processing payment: {payload.method_type} - ${payload.amount}")

    # Simulate payment processing delay
    time.sleep(2)

    # Mock payment success
    payment_success = True
    payment_id = f"pay_{int(time.time())}"

    if not payment_success:
        # Record failed transaction
        create_transaction(
            db,
            user_id=payload.user_id,
            amount=payload.amount,
            type="BOOKING",
            status="FAILED",
            payment_method=payload.method_type,
            reference_id=payload.booking_id,
            note=payload.note,
            method_label=payload.method_label,
            payment_id=payment_id,
        )
        raise HTTPException(
            status_code=400,
            detail="Payment failed: Insufficient funds or payment method declined",
        )

    # If paying via wallet, debit from wallet
    wallet_id = None
    if payload.method_type.upper() == "WALLET":
        wallet = get_or_create_wallet(db, payload.user_id)
        wallet_id = wallet.id
        try:
            wallet_debit(db, payload.user_id, payload.amount)
        except ValueError:
            create_transaction(
                db,
                user_id=payload.user_id,
                amount=payload.amount,
                type="BOOKING",
                status="FAILED",
                payment_method="WALLET",
                reference_id=payload.booking_id,
                note=payload.note,
                method_label=payload.method_label,
                payment_id=payment_id,
            )
            raise HTTPException(
                status_code=400,
                detail="Payment failed: Insufficient wallet balance",
            )

    # Create ticket
    ticket = None
    if payload.trip_id is not None and payload.source_stop_id is not None and payload.destination_stop_id is not None:
        ticket = create_ticket(
            db,
            user_id=payload.user_id,
            trip_id=payload.trip_id,
            seat_id=payload.seat_id or 1,
            source_stop_id=payload.source_stop_id,
            destination_stop_id=payload.destination_stop_id,
            status="PENDING_VALIDATION",
            price=payload.amount,
            passenger_name=payload.passenger_name,
            passenger_phone=payload.passenger_phone,
            passenger_count=payload.passenger_count,
        )

    # Create transaction record (persisted to DB)
    tx = create_transaction(
        db,
        user_id=payload.user_id,
        amount=payload.amount,
        type="BOOKING",
        status="SUCCESSFUL",
        payment_method=payload.method_type,
        wallet_id=wallet_id,
        reference_id=payload.booking_id,
        ticket_id=ticket.id if ticket else None,
        note=payload.note or "Route ticket booking",
        method_label=payload.method_label,
        payment_id=payment_id,
    )

    print(f"✅ Payment processed successfully: {payment_id}")

    ticket_data = None
    if ticket is not None:
        ticket_data = {
            "id": ticket.id,
            "user_id": ticket.user_id,
            "trip_id": ticket.trip_id,
            "source_stop_id": ticket.source_stop_id,
            "destination_stop_id": ticket.destination_stop_id,
            "booking_time": ticket.booking_time.isoformat() if ticket.booking_time else None,
            "expires_at": ticket.expires_at.isoformat() if ticket.expires_at else None,
            "status": ticket.status,
            "price": ticket.price,
            "qr_token": ticket.qr_token,
        }

    return {
        "id": f"tx_{tx.id}",
        "user_id": tx.user_id,
        "amount": tx.amount,
        "type": tx.type,
        "status": tx.status,
        "payment_id": payment_id,
        "ticket": ticket_data,
        "message": "Payment processed successfully",
        "success": True,
    }
