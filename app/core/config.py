import os
from functools import cache
from typing import List

from loguru import logger
from pydantic import AnyHttpUrl, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.settings.database import DatabaseSettings
from app.core.settings.logger import LoggerSettings
from app.core.settings.mongo import MongoDBSettings


class Settings(BaseSettings):
    """Settings class for application settings and secrets management.

    Official documentation on pydantic settings management:
        - https://pydantic-docs.helpmanual.io/usage/settings/
    """

    # Setup the .env file system reading
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")

    # Project details
    APP_NAME: str = "bakky"
    APP_VERSION: str
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    SECRET_KEY: str

    # Default ports and host
    API_ENDPOINT_PORT: int = 8000
    APP_DOCKER_PORT: int = 8042
    API_ENDPOINT_HOST: str = "127.0.0.1"

    # Default API Secrets
    APP_API_KEY: str = "dev"
    APP_API_SECRET: str = ""

    # Application Path
    APP_PATH: str = os.path.abspath(".")
    REPO_PATH: str = os.path.abspath(".")
    CONFIG_PATH: str = os.path.join(APP_PATH, "app", "config")

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Database settings
    DATABASE: DatabaseSettings = DatabaseSettings()

    # MongoDB settings
    MONGODB: MongoDBSettings = MongoDBSettings()

    # Redis settings
    # REDIS: RedisSettings = RedisSettings()

    # Logger settings
    LOGGER: LoggerSettings = LoggerSettings(repo_path=REPO_PATH)

    @classmethod
    @cache
    def get_settings(cls) -> "Settings":
        """Generate and get the settings."""
        try:
            settings = cls()  # noqa
            settings.LOGGER.setup_logger()  # Initialize logger
            return settings
        except ValidationError as e:
            logger.error(f"Validation error in settings: {e}")
            raise  # Raise the validation error to alert the user
        except Exception as message:
            logger.error(f"Error: impossible to get the settings: {message}")
            raise


# default settings with initialization
settings = Settings.get_settings()
