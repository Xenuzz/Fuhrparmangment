"""PDF generation service using Jinja2 HTML templates and WeasyPrint."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.core.config import settings
from app.models.trip import Trip
from app.models.violation import Violation


class PDFService:
    """Renders HTML timesheet templates and exports to A4 PDF bytes."""

    template_root = Path(__file__).resolve().parents[1] / "templates"
    env = Environment(
        loader=FileSystemLoader(template_root),
        autoescape=select_autoescape(["html", "xml"]),
    )

    @classmethod
    def _build_trip_context(cls, trip: Trip, violations: list[Violation]) -> dict[str, object]:
        return {
            "company_name": settings.report_company_name,
            "driver_name": getattr(trip.user, "username", f"Driver #{trip.user_id}"),
            "vehicle": trip.vehicle or "unassigned",
            "job_name": trip.job_name or "unassigned",
            "date_range": f"{trip.start_time.date().isoformat()} - {(trip.end_time or trip.start_time).date().isoformat()}",
            "trips": [
                {
                    "trip_start": trip.start_time.isoformat(),
                    "trip_destination": trip.destination or "N/A",
                    "distance_km": trip.distance_km or 0.0,
                    "driving_time_minutes": trip.driving_time_minutes or 0,
                    "break_time_minutes": trip.break_time_minutes or 0,
                    "total_time_minutes": trip.total_time_minutes or 0,
                    "violations_count": len(violations),
                    "notes": trip.notes or "",
                }
            ],
            "total_violations": len(violations),
            "export_timestamp": datetime.now(UTC).isoformat(),
        }

    @classmethod
    def _build_weekly_context(cls, report: dict[str, object], notes: str = "") -> dict[str, object]:
        rows = report.get("rows", [])
        return {
            "company_name": settings.report_company_name,
            "driver_name": "multiple",
            "vehicle": "multiple",
            "job_name": "multiple",
            "date_range": f"{report.get('from_date')} - {report.get('to_date')}",
            "trips": [
                {
                    "trip_start": row["date"],
                    "trip_destination": row["job_name"],
                    "distance_km": row["total_distance_km"],
                    "driving_time_minutes": row["total_driving_time_minutes"],
                    "break_time_minutes": row["total_break_time_minutes"],
                    "total_time_minutes": row["total_work_time_minutes"],
                    "violations_count": row["total_violations"],
                    "notes": notes,
                }
                for row in rows
            ],
            "total_violations": report.get("totals", {}).get("total_violations", 0),
            "export_timestamp": datetime.now(UTC).isoformat(),
        }

    @classmethod
    def render_timesheet_pdf(cls, context: dict[str, object]) -> bytes:
        """Render timesheet HTML into PDF bytes."""
        template = cls.env.get_template("pdf/timesheet.html")
        html = template.render(**context)
        return HTML(string=html).write_pdf()

    @classmethod
    def generate_trip_timesheet_pdf(cls, trip: Trip, violations: list[Violation]) -> bytes:
        """Generate single-trip timesheet PDF."""
        return cls.render_timesheet_pdf(cls._build_trip_context(trip, violations))

    @classmethod
    def generate_weekly_timesheet_pdf(cls, report: dict[str, object]) -> bytes:
        """Generate weekly-summary timesheet PDF."""
        return cls.render_timesheet_pdf(cls._build_weekly_context(report))
