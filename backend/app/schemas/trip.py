"""Trip-related request and response schemas."""

from datetime import datetime

from pydantic import BaseModel


class TripStartResponse(BaseModel):
    """Response payload for started trip."""

    id: int
    user_id: int
    start_time: datetime


class GPSPointCreate(BaseModel):
    """Request payload for new GPS point."""

    timestamp: datetime
    latitude: float
    longitude: float
    speed_kmh: float


class TripEndResponse(BaseModel):
    """Response payload for ended trip."""

    id: int
    end_time: datetime
    distance_km: float


class GPSPointRead(BaseModel):
    """Response schema for GPS point entries."""

    id: int
    trip_id: int
    timestamp: datetime
    latitude: float
    longitude: float
    speed_kmh: float

    class Config:
        from_attributes = True


class TripRead(BaseModel):
    """Response schema for trip records."""

    id: int
    user_id: int
    start_time: datetime
    end_time: datetime | None
    distance_km: float | None
    gps_points: list[GPSPointRead] = []

    class Config:
        from_attributes = True
