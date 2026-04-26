"""Configuration management for backend services."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    """Database connection values."""

    host: str
    port: int
    name: str
    user: str
    password: str


class DemoUserConfig(BaseModel):
    """Bootstrapped demo user credentials."""

    username: str
    password: str


class ReportsConfig(BaseModel):
    """Report and PDF rendering defaults."""

    company_name: str
    pdf_enabled: bool
    default_timezone: str


class DataQualityConfig(BaseModel):
    """Threshold settings for GPS data quality grading."""

    excellent_filter_rate_percent: float
    good_filter_rate_percent: float
    warning_filter_rate_percent: float


class ViolationsConfig(BaseModel):
    """Tuning values used by speed violation detection."""

    tolerance_kmh: float
    tolerance_percent: float
    grouping_max_gap_seconds: int


class BackendConfig(BaseModel):
    """Backend system settings loaded from JSON config."""

    app_name: str
    app_version: str
    host: str
    port: int
    jwt_secret: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    database: DatabaseConfig
    demo_user: DemoUserConfig


class SystemConfig(BaseModel):
    """Root system configuration model."""

    backend: BackendConfig
    reports: ReportsConfig
    data_quality: DataQualityConfig
    violations: ViolationsConfig


def _load_system_config() -> SystemConfig:
    """Load the global system configuration from mounted config file."""
    root = Path(__file__).resolve().parents[3]
    config_path = root / "config" / "system_config.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return SystemConfig.model_validate(data)


class Settings:
    """Backend settings wrapper with convenient derived values."""

    def __init__(self) -> None:
        cfg = _load_system_config()
        backend = cfg.backend

        self.app_name = backend.app_name
        self.app_version = backend.app_version
        self.host = backend.host
        self.port = backend.port
        self.jwt_secret = backend.jwt_secret
        self.jwt_algorithm = backend.jwt_algorithm
        self.access_token_expire_minutes = backend.access_token_expire_minutes
        self.db_host = backend.database.host
        self.db_port = backend.database.port
        self.db_name = backend.database.name
        self.db_user = backend.database.user
        self.db_password = backend.database.password
        self.demo_username = backend.demo_user.username
        self.demo_password = backend.demo_user.password

        self.report_company_name = cfg.reports.company_name
        self.report_pdf_enabled = cfg.reports.pdf_enabled
        self.report_default_timezone = cfg.reports.default_timezone

        self.dq_excellent_filter_rate_percent = cfg.data_quality.excellent_filter_rate_percent
        self.dq_good_filter_rate_percent = cfg.data_quality.good_filter_rate_percent
        self.dq_warning_filter_rate_percent = cfg.data_quality.warning_filter_rate_percent

        self.violation_tolerance_kmh = cfg.violations.tolerance_kmh
        self.violation_tolerance_percent = cfg.violations.tolerance_percent
        self.violation_grouping_max_gap_seconds = cfg.violations.grouping_max_gap_seconds

    @property
    def sqlalchemy_database_uri(self) -> str:
        """Build SQLAlchemy database URI."""
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
