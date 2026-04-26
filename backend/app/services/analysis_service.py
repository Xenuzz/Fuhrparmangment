"""Trip analysis computation service with GPS data quality filtering."""

from __future__ import annotations

from collections.abc import Sequence

from app.models.break_entry import BreakEntry
from app.models.gps_point import GPSPoint
from app.models.trip import Trip
from app.utils.haversine import haversine_km


class AnalysisService:
    """Provides deterministic analytics for completed trips."""

    MAX_SPEED_KMH = 150.0
    MAX_ACCURACY_M = 50.0
    MAX_JUMP_METERS_PER_SECOND = 100.0

    @classmethod
    def _sort_points(cls, gps_points: Sequence[GPSPoint]) -> list[GPSPoint]:
        """Sort GPS points by timestamp ascending."""
        return sorted(gps_points, key=lambda p: p.timestamp)

    @classmethod
    def _remove_duplicates(cls, gps_points: Sequence[GPSPoint]) -> list[GPSPoint]:
        """Remove duplicate GPS points by keeping first exact sample occurrence."""
        deduped: list[GPSPoint] = []
        seen: set[tuple[str, float, float, float, float | None]] = set()

        for point in gps_points:
            point_key = (
                point.timestamp.isoformat(),
                point.latitude,
                point.longitude,
                point.speed_kmh,
                point.accuracy_m,
            )
            if point_key in seen:
                continue
            seen.add(point_key)
            deduped.append(point)

        return deduped

    @classmethod
    def _apply_filters(cls, gps_points: Sequence[GPSPoint]) -> list[GPSPoint]:
        """Drop implausible GPS points based on speed, accuracy, and jump thresholds."""
        filtered_points: list[GPSPoint] = []

        for point in gps_points:
            if point.speed_kmh > cls.MAX_SPEED_KMH:
                continue

            if point.accuracy_m is not None and point.accuracy_m > cls.MAX_ACCURACY_M:
                continue

            if filtered_points:
                previous = filtered_points[-1]
                delta_seconds = (point.timestamp - previous.timestamp).total_seconds()
                if delta_seconds > 0:
                    segment_distance_m = (
                        haversine_km(
                            previous.latitude,
                            previous.longitude,
                            point.latitude,
                            point.longitude,
                        )
                        * 1000
                    )
                    if delta_seconds <= 1 and segment_distance_m > cls.MAX_JUMP_METERS_PER_SECOND:
                        continue

            filtered_points.append(point)

        return filtered_points

    @classmethod
    def preprocess_gps_points(cls, gps_points: Sequence[GPSPoint]) -> list[GPSPoint]:
        """Run all preprocessing stages for stable analysis calculations."""
        sorted_points = cls._sort_points(gps_points)
        deduped_points = cls._remove_duplicates(sorted_points)
        return cls._apply_filters(deduped_points)

    @classmethod
    def calculate_distance(cls, gps_points: Sequence[GPSPoint]) -> float:
        """Calculate total trip distance in kilometers after data quality filtering."""
        cleaned_points = cls.preprocess_gps_points(gps_points)
        if len(cleaned_points) < 2:
            return 0.0

        total_distance_km = 0.0
        for index in range(1, len(cleaned_points)):
            previous = cleaned_points[index - 1]
            current = cleaned_points[index]
            total_distance_km += haversine_km(
                previous.latitude,
                previous.longitude,
                current.latitude,
                current.longitude,
            )

        return round(total_distance_km, 3)

    @classmethod
    def calculate_driving_time(cls, states: Sequence[GPSPoint]) -> int:
        """Calculate driving time in minutes by summing adjacent valid GPS intervals."""
        cleaned_points = cls.preprocess_gps_points(states)
        if len(cleaned_points) < 2:
            return 0

        total_seconds = 0.0
        for index in range(1, len(cleaned_points)):
            previous = cleaned_points[index - 1]
            current = cleaned_points[index]
            delta_seconds = max((current.timestamp - previous.timestamp).total_seconds(), 0)
            total_seconds += delta_seconds

        return int(round(total_seconds / 60))

    @staticmethod
    def calculate_break_time(breaks: Sequence[BreakEntry]) -> int:
        """Calculate total break duration in minutes."""
        if not breaks:
            return 0

        return sum(max(break_entry.duration_minutes, 0) for break_entry in breaks)

    @staticmethod
    def calculate_total_time(trip: Trip) -> int:
        """Calculate trip total duration in minutes from start to end timestamps."""
        if trip.end_time is None:
            return 0

        duration_seconds = max((trip.end_time - trip.start_time).total_seconds(), 0)
        return int(round(duration_seconds / 60))

    @staticmethod
    def calculate_average_speed(distance: float, driving_time: int) -> float:
        """Calculate average speed in km/h using distance and driving minutes."""
        if driving_time <= 0:
            return 0.0

        return round(distance / (driving_time / 60), 2)

    @classmethod
    def calculate_max_speed(cls, gps_points: Sequence[GPSPoint]) -> float:
        """Calculate maximum valid speed in km/h from filtered GPS points."""
        cleaned_points = cls.preprocess_gps_points(gps_points)
        if not cleaned_points:
            return 0.0

        return round(max(point.speed_kmh for point in cleaned_points), 2)
