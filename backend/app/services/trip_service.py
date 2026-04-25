"""Trip business logic services."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.break_entry import BreakEntry
from app.models.gps_point import GPSPoint
from app.models.trip import Trip
from app.models.user import User
from app.schemas.trip import BreakCreate, GPSPointCreate
from app.utils.haversine import haversine_km


class TripService:
    """Encapsulates trip lifecycle, breaks, and distance calculation workflows."""

    @staticmethod
    def start_trip(db: Session, user: User, auto_started: bool = False) -> Trip:
        """Create and persist a new trip for the given user."""
        trip = Trip(
            user_id=user.id,
            start_time=datetime.now(UTC),
            end_time=None,
            distance_km=None,
            auto_started=auto_started,
            auto_ended=False,
            status="active",
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)
        return trip

    @staticmethod
    def add_gps_point(db: Session, trip: Trip, payload: GPSPointCreate) -> GPSPoint:
        """Persist a GPS point linked to a trip."""
        gps_point = GPSPoint(
            trip_id=trip.id,
            timestamp=payload.timestamp,
            latitude=payload.latitude,
            longitude=payload.longitude,
            speed_kmh=payload.speed_kmh,
        )
        db.add(gps_point)
        db.commit()
        db.refresh(gps_point)
        return gps_point

    @staticmethod
    def add_break(db: Session, trip: Trip, payload: BreakCreate) -> BreakEntry:
        """Create a break and ensure duration is calculated from timestamps when needed."""
        duration = payload.duration_minutes
        if duration is None:
            duration = max(int((payload.end_time - payload.start_time).total_seconds() // 60), 0)

        break_entry = BreakEntry(
            trip_id=trip.id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            duration_minutes=duration,
        )
        db.add(break_entry)
        db.commit()
        db.refresh(break_entry)
        return break_entry

    @staticmethod
    def calculate_trip_distance_km(points: list[GPSPoint]) -> float:
        """Calculate total trip distance by summing segments."""
        if len(points) < 2:
            return 0.0

        sorted_points = sorted(points, key=lambda p: p.timestamp)
        total_distance = 0.0
        for i in range(1, len(sorted_points)):
            prev_point = sorted_points[i - 1]
            curr_point = sorted_points[i]
            total_distance += haversine_km(
                prev_point.latitude,
                prev_point.longitude,
                curr_point.latitude,
                curr_point.longitude,
            )
        return round(total_distance, 3)

    @classmethod
    def end_trip(cls, db: Session, trip: Trip, auto_ended: bool = False) -> Trip:
        """End trip and store calculated distance from recorded points."""
        points = db.query(GPSPoint).filter(GPSPoint.trip_id == trip.id).all()
        trip.distance_km = cls.calculate_trip_distance_km(points)
        trip.end_time = datetime.now(UTC)
        trip.auto_ended = auto_ended
        trip.status = "completed"
        db.commit()
        db.refresh(trip)
        return trip
