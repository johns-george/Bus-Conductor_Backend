from sqlalchemy import Column, BigInteger, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from src.core.database import Base

class RouteStop(Base):
    __tablename__ = "route_stop"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    route_id = Column(BigInteger, ForeignKey("route.id"), nullable=False)
    stop_id = Column(BigInteger, ForeignKey("stops.id"), nullable=False)
    stop_order = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("route_id", "stop_order", name="unique_route_order"),
    )

    route = relationship("Route", back_populates="route_stops")
    stop = relationship("Stop", back_populates="route_stops")