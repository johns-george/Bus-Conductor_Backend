from sqlalchemy import Column, BigInteger, String, Integer
from sqlalchemy.orm import relationship
from src.core.database import Base

class Bus(Base):
    __tablename__ = "bus"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(100))
    bus_number = Column(String(20), unique=True)
    bus_type = Column(String(20), default="non_ac_seater")
    operator_name = Column(String(100))
    capacity = Column(Integer, default=40)
    days = Column(String(50), default="1,2,3,4,5,6,7")  # Comma-separated day numbers: 1=Mon..7=Sun

    bus_routes = relationship("BusRoute", back_populates="bus")