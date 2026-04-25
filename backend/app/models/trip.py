"""Trip model definitions."""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base import Base


class Trip(Base):
    """Represents a truck trip session."""

    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    distance_km = Column(Float, nullable=True)

    user = relationship("User", back_populates="trips")
    gps_points = relationship("GPSPoint", back_populates="trip", cascade="all, delete-orphan")
