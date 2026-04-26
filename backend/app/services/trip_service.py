"""Trip business logic services."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.break_entry import BreakEntry
from app.models.gps_point import GPSPoint
from app.models.trip import Trip
from app.models.user import User
from app.schemas.trip import BreakCreate, GPSPointCreate
from app.services.analysis_service import AnalysisService
from app.services.violation_service import ViolationService


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
            driving_time_minutes=None,
            break_time_minutes=None,
            total_time_minutes=None,
            average_speed_kmh=None,
            max_speed_kmh=None,
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
            accuracy_m=payload.accuracy_m,
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

    @classmethod
    def run_trip_analysis(cls, trip: Trip, points: list[GPSPoint], breaks: list[BreakEntry]) -> None:
        """Compute and assign all analysis fields for persistence on trip end."""
        distance_km = AnalysisService.calculate_distance(points)
        driving_time_minutes = AnalysisService.calculate_driving_time(points)
        break_time_minutes = AnalysisService.calculate_break_time(breaks)
        total_time_minutes = AnalysisService.calculate_total_time(trip)
        average_speed_kmh = AnalysisService.calculate_average_speed(distance_km, driving_time_minutes)
        max_speed_kmh = AnalysisService.calculate_max_speed(points)

        trip.distance_km = distance_km
        trip.driving_time_minutes = driving_time_minutes
        trip.break_time_minutes = break_time_minutes
        trip.total_time_minutes = total_time_minutes
        trip.average_speed_kmh = average_speed_kmh
        trip.max_speed_kmh = max_speed_kmh

    @classmethod
    def end_trip(cls, db: Session, trip: Trip, auto_ended: bool = False) -> Trip:
        """End trip, run analysis pipeline, and persist computed metrics."""
        trip.end_time = datetime.now(UTC)
        trip.auto_ended = auto_ended
        trip.status = "completed"

        points = db.query(GPSPoint).filter(GPSPoint.trip_id == trip.id).all()
        breaks = db.query(BreakEntry).filter(BreakEntry.trip_id == trip.id).all()

        cls.run_trip_analysis(trip, points, breaks)
        ViolationService.persist_trip_violations(db, trip, points)

        db.commit()
        db.refresh(trip)
        return trip
