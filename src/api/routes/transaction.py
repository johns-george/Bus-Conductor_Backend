from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.dao.transaction_dao import (
    get_transactions_by_user,
    get_transaction_by_id,
    retry_transaction,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


class CreateTransactionRequest(BaseModel):
    user_id: int
    amount: float
    status: str = "SUCCESSFUL"
    method_type: str = "UPI"
    booking_id: str | None = None
    ticket_id: str | None = None
    note: str | None = None
    method_label: str | None = None


@router.get("/user/{user_id}")
def transactions_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    type: str | None = Query(None, description="Filter by type: TOPUP, DEBIT, BOOKING, REFUND"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    items = get_transactions_by_user(db, user_id, type=type, limit=limit, offset=offset)
    return {
        "user_id": user_id,
        "items": [
            {
                "id": f"tx_{tx.id}",
                "user_id": tx.user_id,
                "amount": tx.amount,
                "type": tx.type,
                "status": tx.status,
                "method_type": tx.payment_method,
                "payment_method": tx.payment_method,
                "reference_id": tx.reference_id,
                "ticket_id": f"t_{tx.ticket_id}" if tx.ticket_id else None,
                "note": tx.note,
                "method_label": tx.method_label,
                "payment_id": tx.payment_id,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
                "updated_at": tx.updated_at.isoformat() if tx.updated_at else None,
            }
            for tx in items
        ],
        "message": "Transactions list",
    }


@router.get("/{transaction_id}")
def transaction_by_id(transaction_id: str, db: Session = Depends(get_db)):
    numeric_id = int(transaction_id.removeprefix("tx_")) if transaction_id.startswith("tx_") else int(transaction_id)
    tx = get_transaction_by_id(db, numeric_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {
        "id": f"tx_{tx.id}",
        "user_id": tx.user_id,
        "amount": tx.amount,
        "type": tx.type,
        "status": tx.status,
        "method_type": tx.payment_method,
        "payment_method": tx.payment_method,
        "reference_id": tx.reference_id,
        "ticket_id": f"t_{tx.ticket_id}" if tx.ticket_id else None,
        "note": tx.note,
        "method_label": tx.method_label,
        "payment_id": tx.payment_id,
        "created_at": tx.created_at.isoformat() if tx.created_at else None,
        "message": "Transaction detail",
    }


@router.get("/user/{user_id}/payment-methods")
def payment_methods(user_id: int):
    return {
        "user_id": user_id,
        "items": [
            {
                "id": "pm_upi",
                "type": "UPI",
                "label": "UPI",
                "subtitle": "demo@upi",
                "is_default": True,
            },
            {
                "id": "pm_card",
                "type": "CARD",
                "label": "Card",
                "subtitle": "Visa",
                "last_four": "4242",
                "is_default": False,
            },
            {
                "id": "pm_netbanking",
                "type": "NETBANKING",
                "label": "Net Banking",
                "subtitle": "All major banks",
                "is_default": False,
            },
            {
                "id": "pm_wallet",
                "type": "WALLET",
                "label": "Bus Conductor Wallet",
                "subtitle": "Pay from balance",
                "is_default": False,
            },
        ],
        "message": "Payment methods",
    }


@router.post("/{transaction_id}/retry")
def retry(transaction_id: str, db: Session = Depends(get_db)):
    numeric_id = int(transaction_id.removeprefix("tx_")) if transaction_id.startswith("tx_") else int(transaction_id)
    tx = retry_transaction(db, numeric_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {
        "id": f"tx_{tx.id}",
        "user_id": tx.user_id,
        "amount": tx.amount,
        "type": tx.type,
        "status": tx.status,
        "method_type": tx.payment_method,
        "payment_method": tx.payment_method,
        "note": tx.note,
        "created_at": tx.created_at.isoformat() if tx.created_at else None,
        "message": "Transaction retried",
    }
