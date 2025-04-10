import pytest
from loguru import logger

from app.core.config import settings


@pytest.mark.core
def test_settings():
    """Test the settings module."""
    # Check if settings object is not None
    assert settings is not None, "Settings object should be visible and not None"

    assert hasattr(settings, "APP_NAME"), "APP_NAME should exist in settings"

    assert settings.APP_NAME == "bakky", "APP_NAME should be 'bakky'"
    logger.info(f"APP_NAME: {settings.APP_NAME}, LOG_VERBOSITY: {settings.LOGGER.LOG_VERBOSITY}")
    logger.debug(f"APP_NAME: {settings.APP_NAME}, LOG_VERBOSITY: {settings.LOGGER.LOG_VERBOSITY}")


@pytest.mark.core
def test_database_and_mongodb_settings():
    """Test the DATABASE and MONGODB settings."""
    # Check if DATABASE object exists and is not None
    assert hasattr(settings, "DATABASE"), "DATABASE should exist in settings"
    assert settings.DATABASE is not None, "DATABASE object should not be None"

    # Check if MONGODB object exists and is not None
    assert hasattr(settings, "MONGODB"), "MONGODB should exist in settings"
    assert settings.MONGODB is not None, "MONGODB object should not be None"

    # Log the settings for debugging
    logger.info(f"DATABASE: {settings.DATABASE}")
    logger.info(f"MONGODB: {settings.MONGODB}")
