from sqlalchemy import Column, BigInteger, ForeignKey, Time, String, Integer, UniqueConstraint, Text
from sqlalchemy.orm import relationship
from src.core.database import Base

class BusRoute(Base):
    __tablename__ = "bus_route"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bus_id = Column(BigInteger, ForeignKey("bus.id"), nullable=False)
    route_id = Column(BigInteger, ForeignKey("route.id"), nullable=False)
    start_time = Column(Time, nullable=False)
    platform = Column(String(10), default="P1")
    # Comma-separated day abbreviations: mon,tue,wed,thu,fri,sat,sun
    # Empty or NULL means runs every day
    days_of_week = Column(Text, default="mon,tue,wed,thu,fri,sat,sun")

    __table_args__ = (
        UniqueConstraint("bus_id", "route_id", "start_time", name="unique_bus_route_time"),
    )

    bus = relationship("Bus", back_populates="bus_routes")
    route = relationship("Route", back_populates="bus_routes")

    def runs_on_day(self, day_abbr: str) -> bool:
        """Check if this bus runs on the given day (mon, tue, etc.)."""
        if not self.days_of_week:
            return True  # Empty = runs every day
        days = [d.strip().lower() for d in self.days_of_week.split(",")]
        return day_abbr.lower() in days