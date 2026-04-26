"""Speed violation detection service using OpenStreetMap road metadata."""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from typing import Any

import osmnx as ox
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.gps_point import GPSPoint
from app.models.trip import Trip
from app.models.violation import Violation
from app.utils.haversine import haversine_km


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

    @staticmethod
    @lru_cache(maxsize=4096)
    def _lookup_road_data(lat: float, lon: float) -> tuple[Any, Any]:
        """Cache OSM edge lookup by rounded coordinate key for lower OSM overhead."""
        lat_bucket = round(lat, 3)
        lon_bucket = round(lon, 3)
        graph = ViolationService._get_local_road_graph(lat_bucket, lon_bucket)
        u, v, key = ox.nearest_edges(graph, X=lon, Y=lat)
        edge_attrs = graph.get_edge_data(u, v, key) or {}
        return edge_attrs.get("maxspeed"), edge_attrs.get("highway")

    @classmethod
    def match_gps_to_road(cls, gps_point: GPSPoint) -> dict[str, Any]:
        """Find nearest OSM road edge for the provided GPS point."""
        try:
            maxspeed, highway = cls._lookup_road_data(round(gps_point.latitude, 5), round(gps_point.longitude, 5))
            return {"maxspeed": maxspeed, "highway": highway}
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
    def _severity_from_overspeed(cls, overspeed_kmh: float) -> str:
        if overspeed_kmh >= 20:
            return "high"
        if overspeed_kmh >= 10:
            return "medium"
        return "low"

    @classmethod
    def _is_same_group(cls, previous: tuple[GPSPoint, float], current: tuple[GPSPoint, float]) -> bool:
        prev_point, prev_allowed = previous
        curr_point, curr_allowed = current

        gap_seconds = (curr_point.timestamp - prev_point.timestamp).total_seconds()
        if gap_seconds < 0 or gap_seconds > settings.violation_grouping_max_gap_seconds:
            return False

        if abs(curr_allowed - prev_allowed) > max(5.0, prev_allowed * 0.2):
            return False

        distance_km = haversine_km(prev_point.latitude, prev_point.longitude, curr_point.latitude, curr_point.longitude)
        max_plausible_km = (max(prev_point.speed_kmh, curr_point.speed_kmh) * max(gap_seconds, 1)) / 3600 + 0.1
        return distance_km <= max_plausible_km

    @classmethod
    def detect_speed_violations(cls, gps_points: Sequence[GPSPoint]) -> list[dict[str, Any]]:
        """Detect grouped speed violations from ordered GPS samples."""
        if len(gps_points) < 2:
            return []

        sorted_points = sorted(gps_points, key=lambda point: point.timestamp)
        candidate_points: list[tuple[GPSPoint, float]] = []

        for point in sorted_points:
            road_data = cls.match_gps_to_road(point)
            allowed_speed = cls.get_allowed_speed(road_data)
            exceedance_tolerance = max(settings.violation_tolerance_kmh, allowed_speed * (settings.violation_tolerance_percent / 100.0))
            if point.speed_kmh > (allowed_speed + exceedance_tolerance):
                candidate_points.append((point, allowed_speed))

        if not candidate_points:
            return []

        groups: list[list[tuple[GPSPoint, float]]] = []
        active_group: list[tuple[GPSPoint, float]] = [candidate_points[0]]

        for current in candidate_points[1:]:
            if cls._is_same_group(active_group[-1], current):
                active_group.append(current)
            else:
                groups.append(active_group)
                active_group = [current]

        groups.append(active_group)
        return [cls._build_violation_record(group) for group in groups if group]

    @classmethod
    def _build_violation_record(cls, violation_group: list[tuple[GPSPoint, float]]) -> dict[str, Any]:
        """Build a violation record from a grouped violating point span."""
        first_point, _ = violation_group[0]
        last_point, _ = violation_group[-1]

        measured_speed = sum(point.speed_kmh for point, _ in violation_group) / len(violation_group)
        allowed_speed = sum(limit for _, limit in violation_group) / len(violation_group)
        overspeed = max(measured_speed - allowed_speed, 0.0)
        duration_seconds = max(int((last_point.timestamp - first_point.timestamp).total_seconds()), 0)

        return {
            "type": "speed",
            "start_time": first_point.timestamp,
            "end_time": last_point.timestamp,
            "measured_speed_kmh": round(measured_speed, 2),
            "allowed_speed_kmh": round(allowed_speed, 2),
            "overspeed_kmh": round(overspeed, 2),
            "duration_seconds": duration_seconds,
            "latitude": first_point.latitude,
            "longitude": first_point.longitude,
            "severity": cls._severity_from_overspeed(overspeed),
        }

    @classmethod
    def persist_trip_violations(cls, db: Session, trip: Trip, gps_points: Sequence[GPSPoint]) -> None:
        """Persist detected speed violations for a completed trip."""
        db.query(Violation).filter(Violation.trip_id == trip.id).delete()

        for payload in cls.detect_speed_violations(gps_points):
            violation = Violation(trip_id=trip.id, **payload)
            db.add(violation)
