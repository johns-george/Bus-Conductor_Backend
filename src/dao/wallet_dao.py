from datetime import datetime
from sqlalchemy.orm import Session
from src.models.wallet import Wallet


def get_or_create_wallet(db: Session, user_id: int) -> Wallet:
    """Get existing wallet or create one with zero balance."""
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if wallet is None:
        wallet = Wallet(user_id=user_id, balance=0.0, last_updated=datetime.utcnow())
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return wallet


def top_up(db: Session, user_id: int, amount: float) -> Wallet:
    """Add money to wallet and return updated wallet."""
    wallet = get_or_create_wallet(db, user_id)
    wallet.balance += amount
    wallet.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(wallet)
    return wallet


def debit(db: Session, user_id: int, amount: float) -> Wallet:
    """Deduct money from wallet. Raises ValueError if insufficient."""
    wallet = get_or_create_wallet(db, user_id)
    if wallet.balance < amount:
        raise ValueError("Insufficient wallet balance")
    wallet.balance -= amount
    wallet.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(wallet)
    return wallet


def get_balance(db: Session, user_id: int) -> float:
    """Return current wallet balance."""
    wallet = get_or_create_wallet(db, user_id)
    return wallet.balance
