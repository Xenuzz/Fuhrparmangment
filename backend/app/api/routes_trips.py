"""Trip lifecycle and retrieval routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.break_entry import BreakEntry
from app.models.trip import Trip
from app.models.user import User
from app.schemas.trip import (
    BreakCreate,
    BreakRead,
    GPSPointCreate,
    GPSPointRead,
    TripAnalysisRead,
    TripEndRequest,
    TripEndResponse,
    TripRead,
    TripStartRequest,
    TripStartResponse,
)
from app.services.trip_service import TripService

router = APIRouter()


@router.post("/start", response_model=TripStartResponse)
def start_trip(
    payload: TripStartRequest = TripStartRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripStartResponse:
    """Start a new trip for current user."""
    trip = TripService.start_trip(db, current_user, auto_started=payload.auto_started)
    return TripStartResponse(
        id=trip.id,
        user_id=trip.user_id,
        start_time=trip.start_time,
        auto_started=trip.auto_started,
        status=trip.status,
    )


@router.post("/{trip_id}/gps", response_model=GPSPointRead)
def add_gps(
    trip_id: int,
    payload: GPSPointCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GPSPointRead:
    """Append GPS sample to an active trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    if trip.end_time is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trip already ended")

    gps = TripService.add_gps_point(db, trip, payload)
    return GPSPointRead.model_validate(gps)


@router.post("/{trip_id}/breaks", response_model=BreakRead)
def add_break(
    trip_id: int,
    payload: BreakCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BreakRead:
    """Attach a break interval to a trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    break_entry = TripService.add_break(db, trip, payload)
    return BreakRead.model_validate(break_entry)


@router.get("/{trip_id}/breaks", response_model=list[BreakRead])
def list_breaks(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BreakRead]:
    """Return all breaks for a trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    breaks = db.query(BreakEntry).filter(BreakEntry.trip_id == trip.id).order_by(BreakEntry.start_time.asc()).all()
    return [BreakRead.model_validate(item) for item in breaks]


@router.post("/{trip_id}/end", response_model=TripEndResponse)
def end_trip(
    trip_id: int,
    payload: TripEndRequest = TripEndRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripEndResponse:
    """Stop a trip and calculate traveled distance."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    if trip.end_time is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trip already ended")

    trip = TripService.end_trip(db, trip, auto_ended=payload.auto_ended)
    return TripEndResponse(
        id=trip.id,
        end_time=trip.end_time,
        distance_km=trip.distance_km or 0.0,
        auto_ended=trip.auto_ended,
        status=trip.status,
    )


@router.get("", response_model=list[TripRead])
def list_trips(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[TripRead]:
    """Return all user trips."""
    trips = (
        db.query(Trip)
        .options(selectinload(Trip.gps_points), selectinload(Trip.breaks))
        .filter(Trip.user_id == current_user.id)
        .order_by(Trip.start_time.desc())
        .all()
    )
    return [TripRead.model_validate(trip) for trip in trips]


@router.get("/{trip_id}", response_model=TripRead)
def get_trip(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripRead:
    """Return trip detail including GPS trace."""
    trip = (
        db.query(Trip)
        .options(selectinload(Trip.gps_points), selectinload(Trip.breaks))
        .filter(Trip.id == trip_id, Trip.user_id == current_user.id)
        .first()
    )
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return TripRead.model_validate(trip)


@router.get("/{trip_id}/analysis", response_model=TripAnalysisRead)
def get_trip_analysis(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripAnalysisRead:
    """Return persisted trip analysis metrics."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    return TripAnalysisRead(
        id=trip.id,
        distance_km=trip.distance_km or 0.0,
        driving_time_minutes=trip.driving_time_minutes or 0,
        break_time_minutes=trip.break_time_minutes or 0,
        total_time_minutes=trip.total_time_minutes or 0,
        average_speed_kmh=trip.average_speed_kmh or 0.0,
        max_speed_kmh=trip.max_speed_kmh or 0.0,
    )
