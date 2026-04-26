"""Speed violation detection service using OpenStreetMap road metadata."""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from typing import Any

import osmnx as ox
from sqlalchemy.orm import Session

from app.models.gps_point import GPSPoint
from app.models.trip import Trip
from app.models.violation import Violation


class ViolationService:
    """Provides GPS-to-road matching and persistent speed violation detection."""

    FALLBACK_SPEED_BY_HIGHWAY = {
        "residential": 50.0,
        "primary": 100.0,
        "motorway": 130.0,
    }
    DEFAULT_FALLBACK_SPEED = 50.0

    @staticmethod
    @lru_cache(maxsize=256)
    def _get_local_road_graph(lat_bucket: float, lon_bucket: float):
        """Load and cache a local road graph around a coordinate bucket."""
        return ox.graph_from_point((lat_bucket, lon_bucket), dist=350, network_type="drive")

    @classmethod
    def match_gps_to_road(cls, gps_point: GPSPoint) -> dict[str, Any]:
        """Find nearest OSM road edge for the provided GPS point."""
        try:
            lat_bucket = round(gps_point.latitude, 3)
            lon_bucket = round(gps_point.longitude, 3)
            graph = cls._get_local_road_graph(lat_bucket, lon_bucket)
            u, v, key = ox.nearest_edges(graph, X=gps_point.longitude, Y=gps_point.latitude)
            edge_attrs = graph.get_edge_data(u, v, key) or {}
            return {
                "maxspeed": edge_attrs.get("maxspeed"),
                "highway": edge_attrs.get("highway"),
            }
        except Exception:
            return {"maxspeed": None, "highway": None}

    @classmethod
    def get_allowed_speed(cls, road_data: dict[str, Any]) -> float:
        """Resolve allowed speed using OSM maxspeed or highway fallback."""

        def _extract_numeric_kmh(raw_value: Any) -> float | None:
            if raw_value is None:
                return None
            if isinstance(raw_value, list):
                for value in raw_value:
                    parsed = _extract_numeric_kmh(value)
                    if parsed is not None:
                        return parsed
                return None
            if isinstance(raw_value, (int, float)):
                return float(raw_value)

            value_str = str(raw_value).lower().strip()
            digits = "".join(ch for ch in value_str if ch.isdigit() or ch == ".")
            if not digits:
                return None

            numeric_value = float(digits)
            if "mph" in value_str:
                return round(numeric_value * 1.60934, 2)
            return numeric_value

        maxspeed = _extract_numeric_kmh(road_data.get("maxspeed"))
        if maxspeed is not None:
            return maxspeed

        highway = road_data.get("highway")
        if isinstance(highway, list):
            highway = highway[0] if highway else None

        if isinstance(highway, str):
            return cls.FALLBACK_SPEED_BY_HIGHWAY.get(highway, cls.DEFAULT_FALLBACK_SPEED)

        return cls.DEFAULT_FALLBACK_SPEED

    @classmethod
    def detect_speed_violations(cls, gps_points: Sequence[GPSPoint]) -> list[dict[str, Any]]:
        """Detect sustained speed violations from ordered GPS samples."""
        if len(gps_points) < 2:
            return []

        sorted_points = sorted(gps_points, key=lambda point: point.timestamp)
        violations: list[dict[str, Any]] = []
        active_run: list[tuple[GPSPoint, float]] = []

        for point in sorted_points:
            road_data = cls.match_gps_to_road(point)
            allowed_speed = cls.get_allowed_speed(road_data)
            exceedance_tolerance = max(5.0, allowed_speed * 0.10)
            is_violation_point = point.speed_kmh > (allowed_speed + exceedance_tolerance)

            if is_violation_point:
                active_run.append((point, allowed_speed))
                continue

            if len(active_run) > 1:
                violations.append(cls._build_violation_record(active_run))
            active_run = []

        if len(active_run) > 1:
            violations.append(cls._build_violation_record(active_run))

        return violations

    @classmethod
    def _build_violation_record(cls, violation_run: list[tuple[GPSPoint, float]]) -> dict[str, Any]:
        """Build a violation record from a consecutive violating point run."""
        first_point, first_allowed_speed = violation_run[0]
        last_point, _ = violation_run[-1]

        measured_speed = sum(point.speed_kmh for point, _ in violation_run) / len(violation_run)
        allowed_speed = sum(limit for _, limit in violation_run) / len(violation_run)
        exceedance_ratio = (measured_speed - allowed_speed) / max(allowed_speed, 1.0)

        severity = "low"
        if exceedance_ratio >= 0.35:
            severity = "high"
        elif exceedance_ratio >= 0.2:
            severity = "medium"

        return {
            "type": "speed",
            "start_time": first_point.timestamp,
            "end_time": last_point.timestamp,
            "measured_speed_kmh": round(measured_speed, 2),
            "allowed_speed_kmh": round(allowed_speed, 2),
            "latitude": first_point.latitude,
            "longitude": first_point.longitude,
            "severity": severity,
        }

    @classmethod
    def persist_trip_violations(cls, db: Session, trip: Trip, gps_points: Sequence[GPSPoint]) -> None:
        """Persist detected speed violations for a completed trip."""
        db.query(Violation).filter(Violation.trip_id == trip.id).delete()

        for payload in cls.detect_speed_violations(gps_points):
            violation = Violation(trip_id=trip.id, **payload)
            db.add(violation)
