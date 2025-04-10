from contextlib import contextmanager

import psycopg
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


class DBEngine:
    """A class representing a PostgreSQL database engine."""

    def __init__(
        self,
        host: str = settings.db.DB_HOST,
        port: str = settings.db.DB_PORT,
        dbname: str = settings.db.DB_NAME,
        user: str = settings.db.DB_USER,
        password: str = settings.db.DB_PASSWORD.get_secret_value(),
    ):
        """Initializes a new instance of the DBEngine class.

        Args:
            host (str, optional): The host of the PostgreSQL database. Defaults to the value specified in the settings.
            port (str, optional): The port of the PostgreSQL database. Defaults to the value specified in the settings.
            dbname (str, optional): The name of the PostgreSQL database. Defaults to the value specified in the settings.
            user (str, optional): The username for connecting to the PostgreSQL database. Defaults to the value specified in the settings.
            password (str, optional): The password for connecting to the PostgreSQL database. Defaults to the value specified in the settings.
        """
        self.conn_params = {"host": host, "port": port, "dbname": dbname, "user": user, "password": password}

    @contextmanager
    def connect(self):
        """Connects to the PostgreSQL database using the provided connection parameters.

        Returns:
            psycopg.connection: The connection object to the PostgreSQL database.

        Raises:
            psycopg.Error: If an error occurs while connecting to the database.
        """
        conn = None
        try:
            conn = psycopg.connect(autocommit=True, **self.conn_params)
            logger.debug("Connection to PostgresSQL established")
            yield conn
        except psycopg.Error as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            raise
        finally:
            if conn:
                conn.close()
                logger.debug("PostgreSQL connection closed")


class AsyncDBEngine:
    """A class representing an asynchronous database engine for PostgreSQL.

    This class provides methods to connect to a PostgreSQL database using the provided connection parameters.

    Attributes:
        conn_params (dict): A dictionary containing the connection parameters for the PostgreSQL database.

    """

    def __init__(
        self,
        host: str = settings.db.DB_HOST,
        port: str = settings.db.DB_PORT,
        dbname: str = settings.db.DB_NAME,
        user: str = settings.db.DB_USER,
        password: str = settings.db.DB_PASSWORD.get_secret_value(),
    ):
        """Initialize the AsyncDBEngine instance with the provided connection parameters.

        Args:
            host (str, optional): The hostname or IP address of the PostgreSQL server. Defaults to the value specified in the settings.
            port (str, optional): The port number of the PostgreSQL server. Defaults to the value specified in the settings.
            dbname (str, optional): The name of the PostgreSQL database. Defaults to the value specified in the settings.
            user (str, optional): The username for the PostgreSQL connection. Defaults to the value specified in the settings.
            password (str, optional): The password for the PostgreSQL connection. Defaults to the value specified in the settings.

        """
        self.conn_params = {"host": host, "port": port, "dbname": dbname, "user": user, "password": password}

    @contextmanager
    async def connect(self):
        """Connects to the PostgreSQL database using the provided connection parameters.

        This is the asynchronous version of the connect method.

        Returns:
            psycopg.AsyncConnection: The established connection to the PostgreSQL database.

        Raises:
            psycopg.Error: If an error occurs while connecting to the PostgreSQL database.

        """
        aconn = None
        try:
            aconn = await psycopg.AsyncConnection.connect(autocommit=True, **self.conn_params)
            logger.debug("Connection to PostgresSQL established")
            yield aconn
        except psycopg.Error as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            raise
        finally:
            if aconn:
                aconn.close()
                logger.debug("PostgreSQL connection closed")


class AlchemyEngine:
    """A class representing a SQLAlchemy database engine.

    This class provides methods to create a database engine and session using the provided connection parameters.

    SQLAlchemy it's an extra method to launch the query, by default we are using psycopg3.

    Attributes:
        host (str): The host of the database server.
        port (str): The port number of the database server.
        dbname (str): The name of the database.
        user (str): The username for authentication.
        password (str): The password for authentication.
        db_service_string (str): The service string for the database connection.
        engine (sqlalchemy.engine.Engine | None): The database engine.
        session (sqlalchemy.orm.session.sessionmaker | None): The database session.
    """

    def __init__(
        self,
        host: str = settings.db.DB_HOST,
        port: str = settings.db.DB_PORT,
        dbname: str = settings.db.DB_NAME,
        user: str = settings.db.DB_USER,
        password: str = settings.db.DB_PASSWORD.get_secret_value(),
    ):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.db_service_string: str = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"

        self.engine: Engine | None = self.create_db_engine()

    def create_db_engine(self) -> Engine:
        """Create a SQLAlchemy engine."""
        try:
            engine = create_engine(self.db_service_string)
            logger.debug("SQLAlchemy engine created")
            return engine
        except Exception as e:
            logger.error("Failed to create SQLAlchemy engine")
            logger.exception(e)
            raise e

    def create_session(self) -> Session:
        """Create a SQLAlchemy session."""
        try:
            session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)()
            logger.debug("SQLAlchemy session created")
            return session_local
        except Exception as e:
            logger.error("Failed to create SQLAlchemy session")
            logger.exception(e)
            return None

    def check_connection(self) -> bool:
        """Check if the engine is connected to the database."""
        if not self.engine:
            logger.error("Engine is not initialized")
            return False
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                logger.debug("Database connection is valid")
                return True
        except Exception as e:
            logger.error("Failed to connect to the database")
            logger.exception(e)
            return False

    def __enter__(self):
        """Enter the context manager."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the context manager."""
        self.engine.dispose()
