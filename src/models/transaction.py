from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime, String
from datetime import datetime
from src.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=True)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # TOPUP, DEBIT, BOOKING, REFUND
    status = Column(String, default="PENDING")  # PENDING, SUCCESSFUL, FAILED, REFUNDED
    payment_method = Column(String, nullable=True)  # UPI, CARD, NETBANKING, WALLET
    reference_id = Column(String, nullable=True)  # booking_id
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    note = Column(String, nullable=True)
    method_label = Column(String, nullable=True)
    payment_id = Column(String, nullable=True)  # gateway reference
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
