"""Application entry-point for the TruckLog API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes_auth import router as auth_router
from app.api.routes_reports import router as reports_router
from app.api.routes_trips import router as trips_router
from app.core.config import settings
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Run startup bootstrapping tasks."""
    init_db()
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(trips_router, prefix="/trips", tags=["trips"])
app.include_router(reports_router, prefix="/reports", tags=["reports"])


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Return API health status."""
    return {"status": "ok"}
