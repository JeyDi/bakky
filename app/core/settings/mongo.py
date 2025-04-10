from typing import Any, Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MongoDBSettings(BaseSettings):
    """MongoDB connection and configuration settings.

    Uses Pydantic's BaseSettings for automatic environment variable loading.
    All settings can be overridden by environment variables with the prefix MONGO_.

    Example:
        MONGO_URI=mongodb://localhost:27017
        MONGO_DB=my_database
        MONGO_SCHEMAS_DIR=./schemas
    """

    # MongoDB connection settings
    MONGO_URI: str = Field(default="mongodb://localhost:27017", description="MongoDB connection URI")
    MONGO_DB: str = Field(default="test_database", description="MongoDB database name")

    # Authentication settings (optional)
    MONGO_USERNAME: Optional[str] = Field(default="mongo", description="MongoDB username for authentication")
    MONGO_PASSWORD: Optional[str] = Field(default="mongo", description="MongoDB password for authentication")

    # Connection pool settings
    MONGO_MAX_POOL_SIZE: int = Field(default=100, description="Maximum number of connections in the connection pool")
    MONGO_MIN_POOL_SIZE: int = Field(default=0, description="Minimum number of connections in the connection pool")
    MONGO_MAX_IDLE_TIME_MS: int = Field(
        default=0,
        description="Maximum time a connection can remain idle in the pool (0 means no limit)",
    )
    MONGO_CONNECT_TIMEOUT_MS: int = Field(
        default=20000, description="How long to wait for a connection to be established"
    )
    MONGO_SOCKET_TIMEOUT_MS: int = Field(default=20000, description="How long to wait for socket operations")
    MONGO_SERVER_SELECTION_TIMEOUT_MS: int = Field(default=30000, description="How long to wait for server selection")

    # Retry settings
    MONGO_RETRY_WRITES: bool = Field(default=True, description="Enable retryable writes")
    MONGO_RETRY_READS: bool = Field(default=True, description="Enable retryable reads")

    # Other settings
    MONGO_SSL: bool = Field(default=False, description="Enable SSL/TLS for connection")

    def get_connection_args(self) -> Dict[str, Any]:
        """Get MongoDB connection arguments as a dictionary.

        Returns:
            Dict with connection arguments for pymongo.MongoClient
        """
        # Start with basic connection settings
        args = {
            "maxPoolSize": self.MONGO_MAX_POOL_SIZE,
            "minPoolSize": self.MONGO_MIN_POOL_SIZE,
            "connectTimeoutMS": self.MONGO_CONNECT_TIMEOUT_MS,
            "socketTimeoutMS": self.MONGO_SOCKET_TIMEOUT_MS,
            "serverSelectionTimeoutMS": self.MONGO_SERVER_SELECTION_TIMEOUT_MS,
            "retryWrites": self.MONGO_RETRY_WRITES,
            "retryReads": self.MONGO_RETRY_READS,
        }

        # Add authentication settings if provided
        if self.MONGO_USERNAME and self.MONGO_PASSWORD:
            args["username"] = self.MONGO_USERNAME
            args["password"] = self.MONGO_PASSWORD

        # Add SSL/TLS settings if enabled
        if self.MONGO_SSL:
            args["ssl"] = True

        return args

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
