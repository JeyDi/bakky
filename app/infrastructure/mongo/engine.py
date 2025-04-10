from typing import Dict, Optional

from loguru import logger
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.core.config import settings
from app.core.settings.mongo import MongoDBSettings


class MongoDBEngine:
    """MongoDB Engine that manages connections to MongoDB."""

    # Connection cache
    _clients: Dict[str, MongoClient] = {}

    def __init__(self, config: Optional[MongoDBSettings] = None):
        """Initialize MongoDB engine with settings.

        Args:
            settings: MongoDB settings (optional)
        """
        self.config = config or settings.MONGODB
        self._client = None
        self._db = None

    @classmethod
    def get_client(cls, config: MongoDBSettings = None) -> MongoClient:
        """Get a cached standard MongoDB client.

        Args:
            settings: MongoDB settings

        Returns:
            MongoClient instance
        """
        # Use the URI as the cache key
        cache_key = config.URI

        # Create a new client if none exists for this URI
        if cache_key not in cls._clients:
            try:
                # Get connection arguments from settings
                conn_args = config.get_connection_args()

                # Create MongoDB client
                client = MongoClient(config.URI, **conn_args)

                # Check connection is working
                client.admin.command("ping")

                # Store in cache
                cls._clients[cache_key] = client

                logger.info(f"Created new MongoDB client for URI: {config.URI}")
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise

        return cls._clients[cache_key]

    @classmethod
    def close_all_connections(cls):
        """Close all MongoDB connections."""
        # Close connections
        for uri, client in cls._clients.items():
            client.close()
            logger.info(f"Closed MongoDB connection for URI: {uri}")

        # Clear connections
        cls._clients.clear()

        logger.info("Cleared all MongoDB connections")

    @property
    def client(self) -> MongoClient:
        """Get the MongoDB client.

        Returns:
            MongoClient instance
        """
        if not self._client:
            self._client = self.get_client(self.config)
        return self._client

    @property
    def db(self) -> Database:
        """Get the s MongoDB database.

        Returns:
            Database instance
        """
        if not self._db:
            self._db = self.client[self.config.DB]
        return self._db

    def get_collection(self, collection_name: str):
        """Get a MongoDB collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection instance
        """
        return self.db[collection_name]

    def test_connection(self) -> bool:
        """Test the MongoDB connection.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            self.client.admin.command("ping")
            return True
        except Exception as e:
            logger.error(f"MongoDB connection test failed: {e}")
            return False

    def close(self):
        """Close the MongoDB connections for this engine instance."""
        if self._client:
            # Only close if not shared (cached)
            if id(self._client) not in [id(client) for client in self._client.values()]:
                self._client.close()

            self._client = None
            self._db = None
