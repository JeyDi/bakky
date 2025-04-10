from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import Field, root_validator, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    """Redis connection and configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
