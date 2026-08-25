from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, DateTime
from datetime import datetime
from src.core.database import Base


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    method_type = Column(String(20), nullable=False)  # UPI, CARD, NETBANKING
    label = Column(String(100), nullable=False)  # "HDFC Credit Card", "alex@okbi"
    subtitle = Column(String(200))  # "Visa •••• 4421", "Google Pay"
    provider = Column(String(100))  # "HDFC", "SBI", "Google Pay"
    last_four = Column(String(4))  # for cards
    upi_id = Column(String(100))  # for UPI
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
