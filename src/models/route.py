from sqlalchemy import Column, BigInteger, String, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class Route(Base):
    __tablename__ = "route"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(100), nullable=False)

    # # Foreign keys to identify the logical start and end of the route
    start_stop_id = Column(
        BigInteger,
        ForeignKey("stops.id", ondelete="SET NULL"),
        nullable=True
    )
    end_stop_id = Column(
        BigInteger,
        ForeignKey("stops.id", ondelete="SET NULL"),
        nullable=True
    )

    # # Relationship to access the actual Stop objects
    start_stop = relationship(
        "Stop",
        foreign_keys=[start_stop_id],
        back_populates="starting_routes"
    )
    end_stop = relationship(
        "Stop",
        foreign_keys=[end_stop_id],
        back_populates="ending_routes"
    )

    # # Relationship with route_stop table
    route_stops = relationship(
        "RouteStop",
        back_populates="route",
        cascade="all, delete-orphan",
        order_by="RouteStop.stop_order"
    )

    # # Relationship with bus_route table
    bus_routes = relationship(
        "BusRoute",
        back_populates="route",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Route(id={self.id}, name='{self.name}')>"