"""Violation model definitions."""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Violation(Base):
    """Stores detected traffic violations for completed trips."""

    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(64), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    measured_speed_kmh = Column(Float, nullable=False)
    allowed_speed_kmh = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    severity = Column(String(32), nullable=False)

    trip = relationship("Trip", back_populates="violations")
