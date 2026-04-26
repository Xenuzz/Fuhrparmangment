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
    accuracy_m: float | None = None


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
    accuracy_m: float | None

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


class TripAnalysisRead(BaseModel):
    """Response schema with persisted analysis values for a trip."""

    id: int
    distance_km: float
    driving_time_minutes: int
    break_time_minutes: int
    total_time_minutes: int
    average_speed_kmh: float
    max_speed_kmh: float


class ViolationRead(BaseModel):
    """Response payload for trip violation records."""

    id: int
    trip_id: int
    type: str
    start_time: datetime
    end_time: datetime
    measured_speed_kmh: float
    allowed_speed_kmh: float
    latitude: float
    longitude: float
    severity: str

    class Config:
        from_attributes = True


class TripRead(BaseModel):
    """Response schema for trip records."""

    id: int
    user_id: int
    start_time: datetime
    end_time: datetime | None
    distance_km: float | None
    driving_time_minutes: int | None
    break_time_minutes: int | None
    total_time_minutes: int | None
    average_speed_kmh: float | None
    max_speed_kmh: float | None
    auto_started: bool
    auto_ended: bool
    status: str
    gps_points: list[GPSPointRead] = []
    breaks: list[BreakRead] = []

    class Config:
        from_attributes = True
