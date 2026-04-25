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
