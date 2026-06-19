"""
Application configuration — reads from .env via pydantic-settings.
"""

from typing import Any
from urllib.parse import quote, unquote, urlparse, urlunparse

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
        "postgresql+asyncpg://supplyguard:supplyguard@127.0.0.1:5432/supplyguard_db"
    )
    SYNC_DATABASE_URL: str = (
        "postgresql+psycopg2://supplyguard:supplyguard@127.0.0.1:5432/supplyguard_db"
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

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Ensure async SQLAlchemy uses postgresql+asyncpg driver.
        
        If the URL already uses +asyncpg, return it as-is (already correct).
        Otherwise convert plain postgres:// or postgresql:// to +asyncpg and
        safely percent-encode any special characters in the password.
        """
        if not isinstance(v, str):
            return v
        normalized = v.strip().strip('"').strip("'")

        # Already using asyncpg — trust the value as-is, no re-encoding needed
        if "postgresql+asyncpg" in normalized or "postgres+asyncpg" in normalized:
            return normalized

        # Handle plain postgres:// / postgresql:// / postgresql+psycopg2://
        # by re-encoding the password and switching to +asyncpg
        for prefix in (
            "postgres://",
            "postgresql://",
            "postgresql+psycopg2://",
            "postgresql+psycopg2cffi://",
        ):
            if normalized.startswith(prefix):
                remainder = normalized[len(prefix):]
                if "@" in remainder:
                    userinfo, hostinfo = remainder.rsplit("@", 1)
                    if ":" in userinfo:
                        username, password = userinfo.split(":", 1)
                        # unquote first so we don't double-encode
                        safe_password = quote(unquote(password), safe="")
                        normalized = f"postgresql+asyncpg://{username}:{safe_password}@{hostinfo}"
                        return normalized
                # No password — just swap scheme
                return normalized.replace(prefix, "postgresql+asyncpg://", 1)

        return normalized


    @field_validator("SYNC_DATABASE_URL", mode="before")
    @classmethod
    def normalize_sync_database_url(cls, v: str) -> str:
        """Ensure Alembic/sync tooling uses psycopg2 driver."""
        if not isinstance(v, str):
            return v
        normalized = v.strip().strip('"').strip("'")
        if normalized.startswith("postgresql+psycopg2://"):
            return normalized
        if normalized.startswith("postgresql+asyncpg://"):
            return normalized.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        if normalized.startswith("postgresql://"):
            return normalized.replace("postgresql://", "postgresql+psycopg2://", 1)
        if normalized.startswith("postgres://"):
            return normalized.replace("postgres://", "postgresql+psycopg2://", 1)
        return normalized


settings = Settings()
