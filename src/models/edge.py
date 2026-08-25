from sqlalchemy import Column, BigInteger, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class Edge(Base):
    __tablename__ = "edge"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    from_stop = Column(BigInteger, ForeignKey("stops.id"), nullable=False)
    to_stop = Column(BigInteger, ForeignKey("stops.id"), nullable=False)
    distance = Column(Float, nullable=False)

    from_stop_rel = relationship("Stop", foreign_keys=[from_stop], back_populates="outgoing_edges")
    to_stop_rel = relationship("Stop", foreign_keys=[to_stop], back_populates="incoming_edges")