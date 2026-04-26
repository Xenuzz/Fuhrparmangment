"""Report aggregation service for daily and weekly summaries."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.trip import Trip
from app.models.violation import Violation


class ReportService:
    """Builds report rows and totals grouped by date, driver, vehicle, and job."""

    @staticmethod
    def _as_local_date(dt: datetime) -> date:
        tz = ZoneInfo(settings.report_default_timezone)
        return dt.astimezone(tz).date()

    @classmethod
    def _query_base(cls, db: Session, start_date: date, end_date: date, driver_id: int | None, vehicle_id: str | None) -> list[Trip]:
        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=UTC)
        end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time(), tzinfo=UTC)
        query = db.query(Trip).filter(Trip.start_time >= start_dt)
        query = query.filter(Trip.start_time < end_dt)
        if driver_id is not None:
            query = query.filter(Trip.user_id == driver_id)
        if vehicle_id is not None:
            query = query.filter(Trip.vehicle == vehicle_id)
        return query.all()

    @classmethod
    def _aggregate(cls, db: Session, trips: list[Trip]) -> dict[str, object]:
        grouped: dict[tuple[date, int, str, str], dict[str, object]] = {}

        violations_count_by_trip = {
            trip_id: count
            for trip_id, count in (
                db.query(Violation.trip_id, func.count(Violation.id))
                .filter(Violation.trip_id.in_([t.id for t in trips]))
                .group_by(Violation.trip_id)
                .all()
            )
        }

        totals = defaultdict(float)
        totals["total_trips"] = 0

        for trip in trips:
            group_key = (
                cls._as_local_date(trip.start_time),
                trip.user_id,
                trip.vehicle or "unassigned",
                trip.job_name or "unassigned",
            )
            if group_key not in grouped:
                grouped[group_key] = {
                    "date": group_key[0].isoformat(),
                    "driver_id": trip.user_id,
                    "vehicle": group_key[2],
                    "job_name": group_key[3],
                    "total_distance_km": 0.0,
                    "total_driving_time_minutes": 0,
                    "total_break_time_minutes": 0,
                    "total_work_time_minutes": 0,
                    "total_violations": 0,
                    "total_trips": 0,
                }

            row = grouped[group_key]
            row["total_distance_km"] += trip.distance_km or 0.0
            row["total_driving_time_minutes"] += trip.driving_time_minutes or 0
            row["total_break_time_minutes"] += trip.break_time_minutes or 0
            row["total_work_time_minutes"] += trip.total_time_minutes or 0
            row["total_violations"] += int(violations_count_by_trip.get(trip.id, 0))
            row["total_trips"] += 1

            totals["total_distance_km"] += trip.distance_km or 0.0
            totals["total_driving_time_minutes"] += trip.driving_time_minutes or 0
            totals["total_break_time_minutes"] += trip.break_time_minutes or 0
            totals["total_work_time_minutes"] += trip.total_time_minutes or 0
            totals["total_violations"] += int(violations_count_by_trip.get(trip.id, 0))
            totals["total_trips"] += 1

        summary_rows = []
        for row in grouped.values():
            row["total_distance_km"] = round(float(row["total_distance_km"]), 3)
            summary_rows.append(row)

        return {
            "rows": sorted(summary_rows, key=lambda x: (x["date"], x["driver_id"], x["vehicle"], x["job_name"])),
            "totals": {
                "total_distance_km": round(float(totals["total_distance_km"]), 3),
                "total_driving_time_minutes": int(totals["total_driving_time_minutes"]),
                "total_break_time_minutes": int(totals["total_break_time_minutes"]),
                "total_work_time_minutes": int(totals["total_work_time_minutes"]),
                "total_violations": int(totals["total_violations"]),
                "total_trips": int(totals["total_trips"]),
            },
        }

    @classmethod
    def create_daily_report(cls, db: Session, day: date, driver_id: int | None = None, vehicle_id: str | None = None) -> dict[str, object]:
        trips = cls._query_base(db, day, day, driver_id, vehicle_id)
        return {"report_type": "daily", "from_date": day.isoformat(), "to_date": day.isoformat(), **cls._aggregate(db, trips)}

    @classmethod
    def create_weekly_report(cls, db: Session, week_start: date, driver_id: int | None = None, vehicle_id: str | None = None) -> dict[str, object]:
        week_end = week_start + timedelta(days=6)
        trips = cls._query_base(db, week_start, week_end, driver_id, vehicle_id)
        return {
            "report_type": "weekly",
            "from_date": week_start.isoformat(),
            "to_date": week_end.isoformat(),
            **cls._aggregate(db, trips),
        }
