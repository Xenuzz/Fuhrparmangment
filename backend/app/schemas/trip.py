"""Trip-related request and response schemas."""

from datetime import datetime

from pydantic import BaseModel


class TripStartRequest(BaseModel):
    """Request payload for started trip options."""

    auto_started: bool = False


class TripStartResponse(BaseModel):
    """Response payload for started trip."""

    id: int
    user_id: int
    start_time: datetime
    auto_started: bool
    status: str


class GPSPointCreate(BaseModel):
    """Request payload for new GPS point."""

    timestamp: datetime
    latitude: float
    longitude: float
    speed_kmh: float


class TripEndRequest(BaseModel):
    """Request payload for ending trip options."""

    auto_ended: bool = False


class TripEndResponse(BaseModel):
    """Response payload for ended trip."""

    id: int
    end_time: datetime
    distance_km: float
    auto_ended: bool
    status: str


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


class BreakCreate(BaseModel):
    """Request payload for trip break creation."""

    start_time: datetime
    end_time: datetime
    duration_minutes: int | None = None


class BreakRead(BaseModel):
    """Response payload for trip break records."""

    id: int
    trip_id: int
    start_time: datetime
    end_time: datetime
    duration_minutes: int

    class Config:
        from_attributes = True


class TripRead(BaseModel):
    """Response schema for trip records."""

    id: int
    user_id: int
    start_time: datetime
    end_time: datetime | None
    distance_km: float | None
    auto_started: bool
    auto_ended: bool
    status: str
    gps_points: list[GPSPointRead] = []
    breaks: list[BreakRead] = []

    class Config:
        from_attributes = True
