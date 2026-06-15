"""
Application configuration — reads from .env via pydantic-settings.
"""

from typing import List, Any

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "SupplyGuard API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me"

    # Supabase
    SUPABASE_URL: str = "https://your-project-ref.supabase.co"
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://supplyguard:supplyguard@localhost:5432/supplyguard_db"
    )
    SYNC_DATABASE_URL: str = (
        "postgresql+psycopg2://supplyguard:supplyguard@localhost:5432/supplyguard_db"
    )

    # Auth
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS — allow env to provide list, JSON, or comma-separated string
    # Use a permissive type here so the settings source won't attempt to
    # JSON-decode the value before our validator runs.
    ALLOWED_ORIGINS: Any = ["http://localhost:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        # If the env provides a JSON list, pydantic may pass it through as list;
        # handle list, None, empty string and comma-separated string robustly.
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            # Allow comma-separated or JSON-like string
            try:
                # If it's a JSON array string, json.loads will succeed
                import json

                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return [origin.strip() for origin in v.split(",")]
        # Any other type (e.g., already a parsed JSON value) — coerce to list
        try:
            return list(v)
        except Exception:
            return [str(v)]


settings = Settings()
