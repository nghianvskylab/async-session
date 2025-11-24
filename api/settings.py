from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    user: str = "postgres"
    host: str = "localhost"
    port: int = 5432
    name: str = "test_performance"
    password: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


class Settings(BaseSettings):
    database: DatabaseSettings = DatabaseSettings()

    model_config = SettingsConfigDict(
        # Don't read env_file here, let DatabaseSettings handle it
        case_sensitive=False,
    )


settings = Settings()

