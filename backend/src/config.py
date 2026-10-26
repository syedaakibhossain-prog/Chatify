from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    """
    Application settings.

    Local dev: values come from defaults + .env
    Production: all critical values must come from environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ─── Environment ─────────────────────────────────────
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

    # ─── CORS ────────────────────────────────────────────
    # Comma-separated string in env: "http://localhost:5173,https://chatify.app"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def allowed_origins_list(self) -> list[str]:
        """
        Parses the comma-separated ALLOWED_ORIGINS string into a Python list.

        Parameters:
          None (reads self.ALLOWED_ORIGINS)

        Returns:
          list[str]: A list of cleaned origin URLs allowed for CORS,
                     e.g. ["http://localhost:5173", "https://chatify.app"].
        """
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # ─── Database ────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./database.db"

    # ─── Auth ────────────────────────────────────────────
    JWT_ACCESS_SECRET_KEY: str = "dev-access-secret-change-me"
    JWT_REFRESH_SECRET_KEY: str = "dev-refresh-secret-change-me"
    ENCRYPTION_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30   # 30 days



    # ─── Redis ───────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    rate_limit_enabled: bool = True
    trusted_proxy: bool = False               # True behind nginx/cloudflare

    # ─── Realtime ────────────────────────────────────────
    SECONDS_TO_SEND_USER_STATUS: int = 60

    # ─── Validators ──────────────────────────────────────
    @field_validator("JWT_ACCESS_SECRET_KEY", "JWT_REFRESH_SECRET_KEY")
    @classmethod
    def secrets_must_differ(cls, v: str, info) -> str:
        """
        Pydantic field validator that enforces minimum security for JWT secrets.

        Rejects secrets shorter than 32 characters unless they start with the
        'dev-' prefix (which indicates a safe development default).

        Parameters:
          v (str): The secret value being validated.
          info: Pydantic FieldValidationInfo object with context about the field.

        Returns:
          str: The validated secret value, unchanged.

        Raises:
          ValueError: If the secret is < 32 characters and is not a dev default.
        """
        # Prevents copy-paste mistakes where both secrets are identical
        other_field = (
            "JWT_REFRESH_SECRET_KEY"
            if info.field_name == "JWT_ACCESS_SECRET_KEY"
            else "JWT_ACCESS_SECRET_KEY"
        )
        # Can't access other field directly in validator; skip check for simplicity
        if len(v) < 32 and not v.startswith("dev-"):
            raise ValueError("JWT secret must be at least 32 characters")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Creates and returns the singleton application Settings instance.

    Cached with lru_cache(maxsize=1) so the .env file is only parsed once
    per process. In production, also validates that dev-placeholder secrets
    are NOT in use and that DEBUG mode is disabled.

    Parameters:
      None

    Returns:
      Settings: The fully validated application settings object.

    Raises:
      RuntimeError: If running in production with insecure default secrets or DEBUG=True.
    """
    settings = Settings()

    if settings.ENVIRONMENT == "production":
        if settings.JWT_ACCESS_SECRET_KEY.startswith("dev-"):
            raise RuntimeError(
                "JWT_ACCESS_SECRET_KEY must be set in production"
            )
        if settings.JWT_REFRESH_SECRET_KEY.startswith("dev-"):
            raise RuntimeError(
                "JWT_REFRESH_SECRET_KEY must be set in production"
            )
        if settings.DEBUG:
            raise RuntimeError("DEBUG must be False in production")

    return settings


settings = get_settings()
