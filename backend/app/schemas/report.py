"""Reporting schema models."""

from pydantic import BaseModel


class ReportRowRead(BaseModel):
    """Grouped report row."""

    date: str
    driver_id: int
    vehicle: str
    job_name: str
    total_distance_km: float
    total_driving_time_minutes: int
    total_break_time_minutes: int
    total_work_time_minutes: int
    total_violations: int
    total_trips: int


class ReportTotalsRead(BaseModel):
    """Report totals section."""

    total_distance_km: float
    total_driving_time_minutes: int
    total_break_time_minutes: int
    total_work_time_minutes: int
    total_violations: int
    total_trips: int


class ReportRead(BaseModel):
    """Top-level report response."""

    report_type: str
    from_date: str
    to_date: str
    rows: list[ReportRowRead]
    totals: ReportTotalsRead
