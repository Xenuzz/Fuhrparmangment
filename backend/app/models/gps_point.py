"""GPS point model definitions."""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base import Base


class GPSPoint(Base):
    """Stores sampled location data for a trip."""

    __tablename__ = "gps_points"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed_kmh = Column(Float, nullable=False)

    trip = relationship("Trip", back_populates="gps_points")
