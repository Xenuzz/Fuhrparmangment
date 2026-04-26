"""Data quality metrics service for trip GPS analysis."""

from __future__ import annotations

from collections.abc import Sequence

from app.core.config import settings
from app.models.break_entry import BreakEntry
from app.models.gps_point import GPSPoint
from app.models.violation import Violation
from app.services.analysis_service import AnalysisService


class DataQualityService:
    """Computes quality counters and classification for a trip GPS dataset."""

    @staticmethod
    def classify_filter_rate(filter_rate_percent: float) -> str:
        """Map filter rate to configured quality tier."""
        if filter_rate_percent <= settings.dq_excellent_filter_rate_percent:
            return "excellent"
        if filter_rate_percent <= settings.dq_good_filter_rate_percent:
            return "good"
        if filter_rate_percent <= settings.dq_warning_filter_rate_percent:
            return "warning"
        return "bad"

    @classmethod
    def build_metrics(
        cls,
        gps_points: Sequence[GPSPoint],
        breaks: Sequence[BreakEntry],
        violations: Sequence[Violation],
    ) -> dict[str, int | float | str]:
        """Compute raw and derived GPS quality values."""
        total = len(gps_points)
        valid_points = AnalysisService.preprocess_gps_points(gps_points)
        valid = len(valid_points)
        filtered = max(total - valid, 0)
        filter_rate = round((filtered / total * 100.0), 2) if total else 0.0

        return {
            "gps_points_total": total,
            "gps_points_valid": valid,
            "gps_points_filtered": filtered,
            "filter_rate_percent": filter_rate,
            "breaks_total": len(breaks),
            "violations_total": len(violations),
            "analysis_quality": cls.classify_filter_rate(filter_rate),
        }
