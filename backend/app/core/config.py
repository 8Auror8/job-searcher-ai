"""Application settings, loaded exclusively from environment variables (or a .env file)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET = "dev-insecure-secret-change-me-0123456789abcdef"  # noqa: S105 - dev-only default


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    environment: Literal["development", "test", "production"] = "development"
    frontend_url: str = "http://localhost:5173"
    database_url: str = "sqlite+aiosqlite:///./jobpilot.db"

    # Auth
    jwt_secret: str = Field(default=_DEV_SECRET, min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    verify_email_hours: int = 24
    reset_password_minutes: int = 60
    cookie_secure: bool = False

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:5173/api/auth/google/callback"

    # AI (Sprint 2+). Without ANTHROPIC_API_KEY the app still works: CV profiles are filled by hand.
    anthropic_api_key: str = ""
    ai_model_extraction: str = "claude-haiku-5-5"  # ADR-0001: Haiku for high-volume extraction
    ai_daily_calls_per_user: int = 20

    # Email
    resend_api_key: str = ""
    email_from: str = "JobPilot AI <onboarding@resend.dev>"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def ai_enabled(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def google_enabled(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    @model_validator(mode="after")
    def _check_production_safety(self) -> "Settings":
        if self.is_production:
            if self.jwt_secret == _DEV_SECRET:
                raise ValueError("JWT_SECRET must be set in production")
            if not self.cookie_secure:
                raise ValueError("COOKIE_SECURE must be true in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
