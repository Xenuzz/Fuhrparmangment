"""Report and report-timesheet API routes."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.report import ReportRead
from app.services.pdf_service import PDFService
from app.services.report_service import ReportService

router = APIRouter()


@router.get("/daily", response_model=ReportRead)
def get_daily_report(
    date_value: date = Query(alias="date"),
    driver_id: int | None = None,
    vehicle_id: str | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportRead:
    """Return daily aggregated report by day, driver, vehicle, and job."""
    return ReportRead.model_validate(ReportService.create_daily_report(db, date_value, driver_id, vehicle_id))


@router.get("/weekly", response_model=ReportRead)
def get_weekly_report(
    week_start: date,
    driver_id: int | None = None,
    vehicle_id: str | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportRead:
    """Return weekly aggregated report by date, driver, vehicle, and job."""
    return ReportRead.model_validate(ReportService.create_weekly_report(db, week_start, driver_id, vehicle_id))


@router.get("/weekly/timesheet.pdf")
def get_weekly_report_pdf(
    week_start: date,
    driver_id: int | None = None,
    vehicle_id: str | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Export weekly report rows to A4 timesheet PDF."""
    report = ReportService.create_weekly_report(db, week_start, driver_id, vehicle_id)
    pdf_bytes = PDFService.generate_weekly_timesheet_pdf(report)
    return Response(content=pdf_bytes, media_type="application/pdf")
