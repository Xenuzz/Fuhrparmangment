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


def _load_system_config() -> SystemConfig:
    """Load the global system configuration from mounted config file."""
    root = Path(__file__).resolve().parents[3]
    config_path = root / "config" / "system_config.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return SystemConfig.model_validate(data)


class Settings:
    """Backend settings wrapper with convenient derived values."""

    def __init__(self) -> None:
        cfg = _load_system_config().backend
        self.app_name = cfg.app_name
        self.app_version = cfg.app_version
        self.host = cfg.host
        self.port = cfg.port
        self.jwt_secret = cfg.jwt_secret
        self.jwt_algorithm = cfg.jwt_algorithm
        self.access_token_expire_minutes = cfg.access_token_expire_minutes
        self.db_host = cfg.database.host
        self.db_port = cfg.database.port
        self.db_name = cfg.database.name
        self.db_user = cfg.database.user
        self.db_password = cfg.database.password
        self.demo_username = cfg.demo_user.username
        self.demo_password = cfg.demo_user.password

    @property
    def sqlalchemy_database_uri(self) -> str:
        """Build SQLAlchemy database URI."""
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
