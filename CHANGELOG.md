# Changelog

## 2026-04-24

### Added
- Created system-wide JSON configuration at `config/system_config.json` with backend, web UI, and GPS settings.
- Implemented FastAPI backend with clean layering (`api`, `services`, `models`, `schemas`, `db`, `utils`).
- Added PostgreSQL-backed SQLAlchemy models for `User`, `Trip`, and `GPSPoint`.
- Added JWT authentication flow with `/auth/login` endpoint.
- Added trip management endpoints:
  - `POST /trips/start`
  - `POST /trips/{id}/gps`
  - `POST /trips/{id}/end`
  - `GET /trips`
  - `GET /trips/{id}`
- Implemented trip distance calculation using Haversine formula and persisted in `trip.distance_km`.
- Added backend startup database initialization and demo user seeding from configuration.
- Added backend Dockerfile and Python dependencies.
- Implemented React + Vite web UI with pages:
  - Login page
  - Trips list page
  - Trip detail page with Leaflet polyline map
- Added web UI API client and dynamic config loading from `system_config.json`.
- Added web UI Dockerfile for production Nginx serving.
- Implemented Android Kotlin MVP app with:
  - Login screen
  - Start/Stop trip actions
  - Foreground GPS tracking service
  - Local SQLite GPS storage
  - Sync workflow to backend on trip stop
- Added Android Gradle project and resources.
- Added Docker Compose orchestration for `postgres`, `backend`, and `webui` services.

### Updated
- Updated `README.md` title section with project context.

## 2026-04-25

### Added
- Added Android trip automation modules: `TripStateManager`, `MotionDetector`, `PauseDetector`, and `SmartGPSController`.
- Added automated break handling and break sync payload model in Android client.
- Added backend `BreakEntry` model with trip relation and persisted duration tracking.
- Added backend break APIs:
  - `POST /trips/{id}/breaks`
  - `GET /trips/{id}/breaks`
- Added trip schema support for `auto_started`, `auto_ended`, and `status` lifecycle fields.

### Updated
- Upgraded Android `TrackingService` to a resilient foreground orchestration service with:
  - state machine transitions (`IDLE`, `MOVING`, `DRIVING`, `PAUSED`)
  - smart GPS intervals by state
  - background restart behavior
  - automatic trip start/end lifecycle behavior
  - periodic queued point sync every 30-60 seconds with retry bookkeeping
- Updated Android local SQLite queue schema to store sync status and retry metadata.
- Updated Android permissions and service start/stop actions for background stability.
- Updated backend trip service to calculate and store break durations and lifecycle status transitions.
- Updated backend trip routes to expose lifecycle flags and preload breaks in trip reads.
- Updated shared `system_config.json` for v1.1 values and sync timing controls.

## 2026-04-25 (TruckLog v1.2.0)

### Added
- Added backend analysis engine in `analysis_service.py` with stable metrics functions:
  - `calculate_distance(gps_points)`
  - `calculate_driving_time(states)`
  - `calculate_break_time(breaks)`
  - `calculate_total_time(trip)`
  - `calculate_average_speed(distance, driving_time)`
  - `calculate_max_speed(gps_points)`
- Added GPS quality preprocessing pipeline with deterministic ordering and validation:
  - timestamp sorting
  - exact duplicate sample removal
  - invalid point filtering for speed > 150 km/h
  - invalid point filtering for accuracy > 50 m
  - invalid point filtering for distance jumps > 100 m in 1 second
- Added persisted trip analysis attributes to backend `Trip` model:
  - `driving_time_minutes`
  - `break_time_minutes`
  - `total_time_minutes`
  - `average_speed_kmh`
  - `max_speed_kmh`
- Added `GET /trips/{id}/analysis` endpoint for analysis retrieval.
- Added optional `accuracy_m` handling in GPS payload/model for filtering support.

### Updated
- Updated trip end workflow to execute full trip analysis and store all computed values in database.
- Updated backend schemas to expose analysis fields in trip responses.
- Updated web UI trip detail page to display:
  - `distance_km`
  - `driving_time_minutes`
  - `break_time_minutes`
  - `total_time_minutes`
  - `average_speed_kmh`
  - `max_speed_kmh`
- Updated backend app version from `1.1.0` to `1.2.0`.

## 2026-04-26 (TruckLog v1.3.0)

### Added
- Added backend `Violation` persistence model with full trip linkage and location/speed severity fields.
- Added speed violation engine `violation_service.py` with OSM nearest-road lookup and speed-limit parsing.
- Added sustained violation detection requiring multiple consecutive violating GPS points.
- Added speed-limit fallback strategy for missing OSM `maxspeed` using highway defaults:
  - `residential`: 50 km/h
  - `primary`: 100 km/h
  - `motorway`: 130 km/h
- Added tolerance handling for violations using `max(5 km/h, 10%)` over allowed speed.
- Added trip violations API endpoint:
  - `GET /trips/{id}/violations`
- Added frontend trip detail integration for violation loading and count display.
- Added trip map enhancements for:
  - green full-route rendering
  - red violation route segments
  - red violation markers with tooltip data (measured speed, allowed speed, duration)

### Updated
- Updated trip end workflow to detect and persist speed violations.
- Updated backend dependency stack with `osmnx` for local OSM road metadata usage.
- Updated backend app version from `1.2.0` to `1.3.0`.
