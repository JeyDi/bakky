"""Database initialization module.

This module handles database connection verification, schema creation, and health checks.
Can be run as a standalone script or imported and used within FastAPI.
"""

import sys

from loguru import logger

from app.core.config import settings
from app.infrastructure.relational.engine import AlchemyEngine
from app.infrastructure.relational.orm import create_tables


def initialize_orm_tables(alchemy_engine: AlchemyEngine, schema_name: str = "public") -> bool:
    """Initialize ORM tables using the provided Alchemy engine and schema name.

    Args:
        alchemy_engine (AlchemyEngine): An instance of AlchemyEngine used to connect to the database.
        schema_name (str, optional): The name of the schema where the tables will be created. Defaults to "global".

    Returns:
        bool: True if the tables were successfully created, False otherwise.

    The function performs the following steps:
        1. Initializes the Alchemy engine.
        2. Checks if the engine is connected.
        3. If connected, creates the ORM tables in the specified schema.
    """
    # Check if the engine is connected
    if alchemy_engine.check_connection() and alchemy_engine.engine is not None:
        # Create tables
        create_tables(engine=alchemy_engine.engine, schema_name=schema_name)

    return True


def initialize_db() -> None:
    """Run database initialization as a standalone script."""
    try:
        logger.info("Running database initialization as standalone script")
        alchemy_engine = AlchemyEngine()
        success = alchemy_engine.check_connection()

        if success:
            logger.info("Database initialization successful")
            tables_exist = initialize_orm_tables(alchemy_engine)
            {
                "status": "healthy" if tables_exist else "unhealthy",
                "connection": "up",
                "tables": "complete" if tables_exist else "incomplete",
                "database_url": settings.db.connection_string.replace(
                    settings.db.DB_PASSWORD.get_secret_value(), "********"
                ),
                "is_async": False,
            }
            logger.info(f"Database health: {tables_exist}")
        else:
            message = "Database initialization failed, please check your credentials"
            logger.error(message)
            sys.exit(message)
    except Exception as e:
        message = f"An error occurred during database initialization: {e}"
        logger.error(message)
        sys.exit(message)
    finally:
        alchemy_engine.engine.dispose()


if __name__ == "__main__":
    """
    Run this script directly to initialize the database outside of FastAPI.
    
    Example:
    python -m db.initialize
    """
    initialize_db()
