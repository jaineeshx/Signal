"""Application configuration — loaded from environment variables via pydantic-settings."""
from __future__ import annotations

from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """SIGNAL application settings.

    Values are read from the ``.env`` file (if present) and then from
    actual environment variables, with environment variables taking
    precedence.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Gemini AI ──────────────────────────────────────────────────────────
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="Google Gemini API key (from Google AI Studio)",
    )
    gemini_model: str = Field(
        default="gemini-1.5-flash",
        description="Gemini model identifier",
    )
    mock_mode: bool = Field(
        default=False,
        description="When True, skip Gemini calls and return hardcoded mock responses",
    )

    # ── Application ────────────────────────────────────────────────────────
    app_name: str = Field(default="SIGNAL", description="Application display name")
    app_version: str = Field(default="1.0.0", description="Semantic version string")
    debug: bool = Field(default=False, description="Enable verbose debug logging")

    # ── CORS ───────────────────────────────────────────────────────────────
    cors_origins: List[str] = Field(
        default=["http://localhost:8000", "http://127.0.0.1:8000"],
        description="Allowed CORS origins for the API",
    )

    # ── Stadium ────────────────────────────────────────────────────────────
    stadium_name: str = Field(
        default="FIFA World Cup 2026 Venue",
        description="Human-readable stadium name",
    )
    total_capacity: int = Field(
        default=70_000,
        description="Total fan capacity of the stadium",
        gt=0,
    )

    @property
    def gemini_available(self) -> bool:
        """Return True when a real Gemini key is configured and mock mode is off."""
        return bool(self.gemini_api_key) and not self.mock_mode


# Module-level singleton — import this everywhere
settings = Settings()
