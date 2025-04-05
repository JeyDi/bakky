from app.core.config import settings
from loguru import logger
import pytest


@pytest.mark.core
def test_settings():
    # Check if settings object is not None
    assert settings is not None, "Settings object should be visible and not None"

    assert hasattr(settings, "APP_NAME"), "APP_NAME should exist in settings"

    assert settings.APP_NAME == "bakky", "APP_NAME should be 'bakky'"
    logger.info(f"APP_NAME: {settings.APP_NAME}, LOG_VERBOSITY: {settings.LOGGER.LOG_VERBOSITY}")
    logger.debug(f"APP_NAME: {settings.APP_NAME}, LOG_VERBOSITY: {settings.LOGGER.LOG_VERBOSITY}")
