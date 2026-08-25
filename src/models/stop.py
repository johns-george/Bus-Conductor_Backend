from sqlalchemy import Column, BigInteger, String, Float
from sqlalchemy.orm import relationship
from src.core.database import Base

class Stop(Base):
    __tablename__ = "stops"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255))
    area = Column(String(100))
    city = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)

    # -----------------------------
    # Graph relationships
    # -----------------------------
    outgoing_edges = relationship(
        "Edge",
        foreign_keys="Edge.from_stop",
        back_populates="from_stop_rel"
    )
    incoming_edges = relationship(
        "Edge",
        foreign_keys="Edge.to_stop",
        back_populates="to_stop_rel"
    )

    # -----------------------------
    # RouteStop relationship
    # -----------------------------
    route_stops = relationship(
        "RouteStop",
        back_populates="stop",
        cascade="all, delete-orphan"
    )

    # -----------------------------
    # Reverse relationships for Route
    # -----------------------------
    starting_routes = relationship(
        "Route",
        foreign_keys="Route.start_stop_id",
        back_populates="start_stop"
    )

    ending_routes = relationship(
        "Route",
        foreign_keys="Route.end_stop_id",
        back_populates="end_stop"
    )

    def __repr__(self):
        return f"<Stop(id={self.id}, name='{self.name}')>"