from datetime import datetime
from sqlalchemy.orm import Session
from src.models.transaction import Transaction


def create_transaction(
    db: Session,
    *,
    user_id: int,
    amount: float,
    type: str,
    status: str = "SUCCESSFUL",
    payment_method: str | None = None,
    wallet_id: int | None = None,
    reference_id: str | None = None,
    ticket_id: int | None = None,
    note: str | None = None,
    method_label: str | None = None,
    payment_id: str | None = None,
) -> Transaction:
    """Create and persist a new transaction record."""
    tx = Transaction(
        user_id=user_id,
        wallet_id=wallet_id,
        amount=amount,
        type=type,
        status=status,
        payment_method=payment_method,
        reference_id=reference_id,
        ticket_id=ticket_id,
        note=note,
        method_label=method_label,
        payment_id=payment_id,
        created_at=datetime.utcnow(),
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def get_transactions_by_user(
    db: Session,
    user_id: int,
    type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Transaction]:
    """Get all transactions for a user, optionally filtered by type."""
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    if type:
        query = query.filter(Transaction.type == type)
    return query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()


def get_transaction_by_id(db: Session, transaction_id: int) -> Transaction | None:
    """Get a single transaction by its ID."""
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()


def retry_transaction(db: Session, transaction_id: int) -> Transaction | None:
    """Retry a failed transaction by resetting its status to SUCCESSFUL."""
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if tx is None:
        return None
    tx.status = "SUCCESSFUL"
    tx.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(tx)
    return tx
