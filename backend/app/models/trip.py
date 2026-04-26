"""Trip model definitions."""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
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
    driving_time_minutes = Column(Integer, nullable=True)
    break_time_minutes = Column(Integer, nullable=True)
    total_time_minutes = Column(Integer, nullable=True)
    average_speed_kmh = Column(Float, nullable=True)
    max_speed_kmh = Column(Float, nullable=True)
    vehicle = Column(String(128), nullable=True)
    job_name = Column(String(128), nullable=True)
    destination = Column(String(256), nullable=True)
    notes = Column(Text, nullable=True)
    auto_started = Column(Boolean, nullable=False, default=False)
    auto_ended = Column(Boolean, nullable=False, default=False)
    status = Column(String(32), nullable=False, default="active")

    user = relationship("User", back_populates="trips")
    gps_points = relationship("GPSPoint", back_populates="trip", cascade="all, delete-orphan")
    breaks = relationship("BreakEntry", back_populates="trip", cascade="all, delete-orphan")
    violations = relationship("Violation", back_populates="trip", cascade="all, delete-orphan")
