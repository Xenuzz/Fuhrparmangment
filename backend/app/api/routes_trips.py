"""Trip lifecycle and retrieval routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.trip import Trip
from app.models.user import User
from app.schemas.trip import GPSPointCreate, GPSPointRead, TripEndResponse, TripRead, TripStartResponse
from app.services.trip_service import TripService

router = APIRouter()


@router.post("/start", response_model=TripStartResponse)
def start_trip(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> TripStartResponse:
    """Start a new trip for current user."""
    trip = TripService.start_trip(db, current_user)
    return TripStartResponse(id=trip.id, user_id=trip.user_id, start_time=trip.start_time)


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


@router.post("/{trip_id}/end", response_model=TripEndResponse)
def end_trip(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripEndResponse:
    """Stop a trip and calculate traveled distance."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    if trip.end_time is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trip already ended")

    trip = TripService.end_trip(db, trip)
    return TripEndResponse(id=trip.id, end_time=trip.end_time, distance_km=trip.distance_km or 0.0)


@router.get("", response_model=list[TripRead])
def list_trips(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[TripRead]:
    """Return all user trips."""
    trips = (
        db.query(Trip)
        .options(selectinload(Trip.gps_points))
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
        .options(selectinload(Trip.gps_points))
        .filter(Trip.id == trip_id, Trip.user_id == current_user.id)
        .first()
    )
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return TripRead.model_validate(trip)
