import time
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.dao.wallet_dao import get_or_create_wallet, top_up, debit
from src.dao.transaction_dao import create_transaction

router = APIRouter(prefix="/wallet", tags=["wallet"])


class WalletAmountRequest(BaseModel):
    amount: float
    note: str | None = None


class WalletTopupPaymentRequest(BaseModel):
    amount: float
    method_type: str
    method_id: str | None = None
    method_label: str | None = None


@router.get("/{user_id}")
def wallet_by_user(user_id: int, db: Session = Depends(get_db)):
    wallet = get_or_create_wallet(db, user_id)
    return {
        "user_id": wallet.user_id,
        "balance": wallet.balance,
        "currency": wallet.currency,
        "last_updated": wallet.last_updated.isoformat() if wallet.last_updated else None,
        "message": "Wallet detail",
    }


@router.post("/{user_id}/topup")
def wallet_topup(user_id: int, payload: WalletAmountRequest, db: Session = Depends(get_db)):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    wallet = top_up(db, user_id, payload.amount)

    create_transaction(
        db,
        user_id=user_id,
        amount=payload.amount,
        type="TOPUP",
        status="SUCCESSFUL",
        payment_method="WALLET_TOPUP",
        wallet_id=wallet.id,
        note="Wallet top-up",
        method_label="Wallet",
    )

    return {
        "user_id": wallet.user_id,
        "balance": wallet.balance,
        "currency": wallet.currency,
        "last_updated": wallet.last_updated.isoformat() if wallet.last_updated else None,
        "action": "TOPUP",
        "message": "Wallet top-up successful",
    }


@router.post("/{user_id}/topup-via-payment")
def wallet_topup_via_payment(user_id: int, payload: WalletTopupPaymentRequest, db: Session = Depends(get_db)):
    """Process wallet top-up through a payment method (UPI, Card, Net Banking)."""
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    print(f"💳 Processing wallet top-up: ₹{payload.amount} via {payload.method_type}")

    # Simulate payment processing delay
    time.sleep(2)

    payment_id = f"pay_{int(time.time())}"
    payment_success = True  # Mock — always succeeds

    if not payment_success:
        create_transaction(
            db,
            user_id=user_id,
            amount=payload.amount,
            type="TOPUP",
            status="FAILED",
            payment_method=payload.method_type,
            note="Wallet top-up failed",
            method_label=payload.method_label,
            payment_id=payment_id,
        )
        raise HTTPException(status_code=400, detail="Payment failed: Payment method declined")

    # Credit wallet
    wallet = top_up(db, user_id, payload.amount)

    # Record successful transaction
    create_transaction(
        db,
        user_id=user_id,
        amount=payload.amount,
        type="TOPUP",
        status="SUCCESSFUL",
        payment_method=payload.method_type,
        wallet_id=wallet.id,
        note="Wallet top-up",
        method_label=payload.method_label,
        payment_id=payment_id,
    )

    print(f"✅ Wallet top-up successful: {payment_id}")

    return {
        "user_id": wallet.user_id,
        "balance": wallet.balance,
        "currency": wallet.currency,
        "last_updated": wallet.last_updated.isoformat() if wallet.last_updated else None,
        "payment_id": payment_id,
        "method_type": payload.method_type,
        "action": "TOPUP",
        "message": "Wallet top-up successful",
    }


@router.post("/{user_id}/debit")
def wallet_debit(user_id: int, payload: WalletAmountRequest, db: Session = Depends(get_db)):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    try:
        wallet = debit(db, user_id, payload.amount)
    except ValueError:
        raise HTTPException(status_code=400, detail="Insufficient wallet balance")

    create_transaction(
        db,
        user_id=user_id,
        amount=payload.amount,
        type="DEBIT",
        status="SUCCESSFUL",
        payment_method="WALLET",
        wallet_id=wallet.id,
        note=payload.note or "Wallet debit",
        method_label="Wallet",
    )

    return {
        "user_id": wallet.user_id,
        "balance": wallet.balance,
        "currency": wallet.currency,
        "last_updated": wallet.last_updated.isoformat() if wallet.last_updated else None,
        "action": "DEBIT",
        "message": "Wallet debited",
    }
