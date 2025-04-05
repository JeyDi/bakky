from typing import Optional

from pydantic import Field, PostgresDsn, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    # PostgreSQL connection parameters
    DB_USER: str = Field(default="postgres")
    DB_PASSWORD: SecretStr = Field(default="postgres")
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=5432)
    DB_NAME: str = Field(default="bakky")

    # Optional direct connection string (overrides individual params if provided)
    DATABASE_URL: Optional[PostgresDsn] = None

    # Additional connection settings
    DB_SSL_MODE: Optional[str] = Field(default=None)
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)
    DB_POOL_RECYCLE: int = Field(default=3600)  # 1 hour

    PROFILE: bool = False

    @computed_field
    def connection_string(self) -> str:
        """Get the full PostgreSQL connection string using psycopg3."""
        if self.DATABASE_URL:
            # Directly return the provided connection string if available
            return str(self.DATABASE_URL)

        # Build connection string from parameters
        password = self.DB_PASSWORD.get_secret_value()
        url = f"postgresql+psycopg://{self.DB_USER}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

        # Add SSL mode if specified
        if self.DB_SSL_MODE:
            url += f"?sslmode={self.DB_SSL_MODE}"

        return url

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
