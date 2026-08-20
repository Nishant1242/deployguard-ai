from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "DeployGuard AI API"
    app_version: str = "0.2.0"
    environment: str = "development"
    debug: bool = False

    database_url: SecretStr
    database_pool_size: int = Field(default=5, ge=1, le=20)
    database_max_overflow: int = Field(default=10, ge=0, le=40)
    database_pool_timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=120,
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(
        cls,
        value: SecretStr,
    ) -> SecretStr:
        """Require the approved PostgreSQL Psycopg connection scheme."""

        try:
            url = make_url(value.get_secret_value())
        except ArgumentError as error:
            raise ValueError("DATABASE_URL must be a valid SQLAlchemy URL.") from error

        if url.drivername != "postgresql+psycopg":
            raise ValueError("DATABASE_URL must use postgresql+psycopg.")

        if not url.database:
            raise ValueError("DATABASE_URL must include a database name.")

        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Create and cache one settings object for the application."""

    return Settings()
