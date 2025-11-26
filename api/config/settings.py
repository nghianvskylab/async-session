"""
Application configuration settings leveraging pydantic-settings.
"""

import os
from typing import Final

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _optional_secret_from_env(var_name: str) -> SecretStr | None:
    """Return `SecretStr` when env var exists, otherwise `None`."""
    value = os.getenv(var_name)
    return SecretStr(value) if value is not None else None


class DatabaseSettings(BaseSettings):
    user: str = "postgres"
    host: str = "localhost"
    port: int = 5432
    name: str = ""
    password: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class Settings(BaseSettings):
    APP_NAME: str = "Base FastAPI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str | None = None
    DATABASE_ECHO: bool = False

    ALLOWED_ORIGINS: list[str] | str = Field(default_factory=lambda: ["*"])

    LOG_LEVEL: str = "INFO"
    LOG_RETENTION_DAYS: int = 30

    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = 30

    database: DatabaseSettings = DatabaseSettings()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def default_database_url(cls, value: str | None) -> str:
        if value:
            return value
        db = DatabaseSettings()
        return (
            f"postgresql+asyncpg://{db.user}:"
            f"{db.password.get_secret_value() if db.password else ''}"
            f"@{db.host}:{db.port}/{db.name}"
        )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: str | list[str] | None) -> list[str]:
        if value is None:
            return ["*"]
        if isinstance(value, list):
            return value
        cleaned = value.strip()
        if cleaned.startswith("[") and cleaned.endswith("]"):
            cleaned = cleaned[1:-1]
        return [
            origin.strip().strip('"').strip("'")
            for origin in cleaned.split(",")
            if origin.strip()
        ]


settings = Settings()
