from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Float
from datetime import datetime
from src.core.database import Base
from pydantic import BaseModel
from typing import Optional

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)  # you can link later if user table exists
    trip_id = Column(Integer, ForeignKey("route.id"))

    source_stop_id = Column(Integer, ForeignKey("stops.id"))
    destination_stop_id = Column(Integer, ForeignKey("stops.id"))

    booking_time = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    status = Column(String, default="CONFIRMED")
    price = Column(Float, default=0.0)
    qr_token = Column(String(512), nullable=True)
    validated_by = Column(Integer, nullable=True)  # conductor user ID
    validated_at = Column(DateTime, nullable=True)
    passenger_name = Column(String(255), nullable=True)
    passenger_phone = Column(String(20), nullable=True)
    passenger_count = Column(Integer, default=1)

    @property
    def time_of_travel(self):
        return self.booking_time

class TicketUpdate(BaseModel):
    price: Optional[float] = None
    status: Optional[str] = None
    destination_stop_id: Optional[int] = None
    passenger_name: Optional[str] = None
    passenger_phone: Optional[str] = None
    passenger_count: Optional[int] = None
