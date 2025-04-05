import os
import sys

from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggerSettings(BaseSettings):
    """Logger configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    LOG_VERBOSITY: str = "DEBUG"
    LOG_ROTATION_SIZE: str = "100MB"
    LOG_RETENTION: str = "30 days"
    LOG_FOLDER: str = os.path.join(super.REPO_PATH, "logs")
    LOG_FILE_NAME: str = "bakky_{time:D-M-YY}.log"
    LOG_FILE_PATH: str = os.path.join(LOG_FOLDER, LOG_FILE_NAME)
    LOG_FORMAT: str = "{level}\t|  {time:HH:mm:ss!UTC} utc  |  {file}:{module}:{line}  |  {message}"

    def setup_logger(self):
        """Configure the logger."""
        logger.remove()  # Remove previous handlers
        logger.add(
            sink=sys.stderr,
            colorize=True,
            format=self.LOG_FORMAT,
            level=self.LOG_VERBOSITY,
            serialize=False,
            catch=True,
            backtrace=False,
            diagnose=False,
        )
        logger.add(
            sink=self.LOG_FILE_PATH,
            rotation=self.LOG_ROTATION_SIZE,
            retention=self.LOG_RETENTION,
            colorize=True,
            format=self.LOG_FORMAT,
            level=self.LOG_VERBOSITY,
            serialize=False,
            catch=True,
            backtrace=False,
            diagnose=False,
            encoding="utf8",
        )
