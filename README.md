# Fuhrparmangment

TruckLog v1.4 monorepo including:
- FastAPI backend with PostgreSQL, JWT auth, reporting endpoints, data quality analytics, and PDF timesheet export.
- Android app for trip tracking, queued GPS synchronization, and a lightweight debug/status panel.
- React + Leaflet web UI with trip details, quality panel, violation severity display, and a new reports page.
- Docker Compose stack for backend, database, and web UI.

## New in v1.4

### Backend
- Daily and weekly reports:
  - `GET /reports/daily`
  - `GET /reports/weekly`
- Timesheet PDF export:
  - `GET /trips/{id}/timesheet.pdf`
  - `GET /reports/weekly/timesheet.pdf`
- Data quality endpoint:
  - `GET /trips/{id}/quality`
- Improved violation detection with OSM lookup caching, grouped violations, and severity classification.

### Web UI
- Trip detail page now includes:
  - PDF export button
  - data quality panel
  - enhanced violation detail list
- Added `/reports` page with daily/weekly summary tables and weekly PDF export.

### Android
- Added small debug/status panel showing:
  - current tracking state
  - GPS points recorded
  - last sync status
  - unsynced queue count

## PDF Dependencies
The backend uses **WeasyPrint** and requires these system packages in Docker:
- `libcairo2`
- `libpango-1.0-0`
- `libpangocairo-1.0-0`
- `libgdk-pixbuf-2.0-0`
- `libffi-dev`
- `shared-mime-info`
