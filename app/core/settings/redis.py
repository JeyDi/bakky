from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    """Redis connection and configuration settings."""

    # Redis connection settings
    REDIS_HOST: str = Field(default="http://localhost", description="Redis server hostname or IP address")
    REDIS_PORT: int = Field(default=6379, description="Redis server port")
    REDIS_PASSWORD: str = Field(default="bakky", description="Password for Redis authentication")
    REDIS_DB: int = Field(default=0, description="Redis database index")
    REDIS_SSL: bool = Field(default=False, description="Enable SSL for Redis connection")

    # Redis connection pool settings
    REDIS_MAX_CONNECTIONS: int = Field(
        default=10, description="Maximum number of connections in the Redis connection pool"
    )
    REDIS_TIMEOUT: int = Field(default=5, description="Timeout for Redis operations in seconds")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
