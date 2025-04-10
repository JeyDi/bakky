import os
from collections.abc import Generator
from pathlib import Path
from typing import List

import psycopg
from loguru import logger
from psycopg import sql
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.src.config import settings
from app.src.db.engine import AlchemyEngine, DBEngine
from app.src.utils.files import read_yaml


def get_session(session_local: sessionmaker) -> Generator:
    """Get a specific session for the database using SQLAlchemy.

    This function it's usefull only if you are using the database in ORM mode.
    The function create a Generator object that you can export and use everywhere in the code, especially when you are trying to use FastAPI.

    Args:
        session_local: SQLAlchemy sessions object

    Returns:
        yield Session
    """
    try:
        session = session_local()
        yield session
    finally:
        session.close()  # type: ignore


def create_connection(
    connection_type: str,
    return_session: bool = False,
    host: str = settings.DB_HOST,
    port: str = settings.DB_PORT,
    dbname: str = settings.DB_NAME,
    user: str = settings.DB_USER,
    password: str = settings.DB_PASSWORD,
) -> Engine:
    """This is a generic create connection for sqlalchemy and psycopg3.

    You can override the default configuration that you can write into .env and config file.

    Connection type
    - `sqlalchemy`: Use the SQLAlchemy engine to connect to the database
    - `psycopg`: Use the psycopg3 engine to connect to the database

    You can use the session object to generate the session generator with the function get_session()

    Args:
        connection_type (str): sqlalchemy or psycopg connection
        return_session (bool): if True, return the session object for sqlalchemy, else return only the sqlalchemy engine.
            This parameter it's used only for sqlalchemy connection
        host (str): override default config Host of the database
        port (str): override default config Port of the database
        dbname (str): override default config  Database name
        user (str): override default config User of the database
        password (str): override default config Password of the database

    Returns:
        engine (object): the sqlalchemy engine object
        session (object): the sqlalchemy session object (created with sessionmaker)
    """
    try:
        if connection_type.lower().strip() in ["sqlalchemy", "alchemy"]:
            engine = AlchemyEngine(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password,
            )

            if return_session:
                return engine.get_session()
            # only return the sqlalchemy engine without the session
            return engine.get_engine()
        if connection_type.lower().strip() in ["psycopg", "normal", "psycopg3", "psycopg2"]:
            return DBEngine(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password,
            )

        logger.exception(f"Impossible to connect to the db using {connection_type} connection")
        raise
    except Exception as message:
        logger.error(f"Impossible to connect to the db using {connection_type} connection")
        logger.exception(f"Error creating the engine: {message}")
        raise


def execute_query(
    *, engine: DBEngine | None = DBEngine(), query, params: tuple | None = None, fetch_results: bool = False
) -> list | bool | None:
    """Executes the given query using the provided database engine.

    Args:
        engine (DBEngine | None, optional): The database engine to use for executing the query. Defaults to DBEngine().
        query (str): The SQL query to execute.
        params (tuple, optional): The parameters to be used in the query. Defaults to None.
        fetch_results (bool, optional): If True, the query results will be fetched. Defaults to False.

    Returns:
        bool: True if the query was executed successfully, False otherwise.
    """
    if engine is None:
        engine = DBEngine()
    with engine.connect() as conn:
        try:
            cur = conn.cursor()
            with conn.transaction():
                cur.execute(query, params)
            if fetch_results:
                # Retrieve query results
                records = cur.fetchall()
                logger.debug(f"Query executed: {query}")
                return records
            else:  # noqa: RET505
                logger.debug(f"Query executed: {query}")
                return True
        except psycopg.Error as e:
            logger.error(f"Error executing query: {e}")
            conn.rollback()
            if fetch_results:
                return None
            else:  # noqa: RET505
                return False


def create_db(*, engine: DBEngine = DBEngine(dbname="postgres"), db_name: str) -> bool:
    """Create a new postgres database.

    By default the function use the default database `postgres` to create a new database.

    Args:
        engine (DBEngine , optional): The database engine to use for executing the query. Defaults to DBEngine(dbname="postgres").
        db_name (str): db name to create.

    Returns:
        bool: True if the query was executed successfully, False otherwise.
    """
    check_query = sql.SQL("SELECT 1 FROM pg_database WHERE datname = {database}").format(database=db_name)
    create_query = f"""
    CREATE DATABASE {db_name}
    OWNER {settings.DB_USER}
    ENCODING 'UTF8';
    """

    with engine.connect() as conn:
        try:
            cur = conn.cursor()
            # Check if the database already exists
            logger.debug(f"Executing query: {check_query}")
            cur.execute(check_query)
            if cur.fetchone() is not None:
                # Database already exists
                logger.debug(f"Database {db_name} already exists.")
                return True

            # Database does not exist, create it
            logger.debug(f"Executing query: {create_query}")
            cur.execute(create_query)
            conn.commit()
            logger.debug(f"Created database: {db_name}")
            return True
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            conn.rollback()
            return False


def read_table_schema(file_path: str, file_name: str) -> dict:
    """Reads the table schema from a YAML file.

    Args:
        file_path (str): The path to the directory containing the YAML file.
        file_name (str): The name of the YAML file.

    Returns:
        dict: A dictionary representing the table schema.

    """
    return read_yaml(file_path, file_name)


def psycopg_connection_string() -> str:
    """Generate a connection string for PostgreSQL using the settings from the configuration file.

    Returns:
        str: The connection string for PostgreSQL.
    """
    # Create the connection string manually
    return f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"


def get_primary_key_columns(*, engine: DBEngine = DBEngine(), table_name: str, schema: str = "public") -> List[str]:
    """Retrieve the name of the column with the specified primary key.

    Args:
        engine: The database engine to use for executing the query.
        table_name: name of the table
        schema: The name of the schema containing the table.

    Returns:
        List[str]: The name of the column with the primary key.
    """
    # clean the schema
    if schema != "public":
        schema = schema.lower().replace("-", "_").strip()

    # compose the query
    query = sql.SQL(
        """
    SELECT a.attname
    FROM pg_index i
    JOIN pg_attribute a ON a.attrelid = i.indrelid
    AND a.attnum = ANY(i.indkey)
    WHERE i.indrelid = {table_name}::regclass
    AND i.indisprimary;
    """
    ).format(table_name=sql.Literal(schema + "." + table_name))

    # launch the query
    try:
        with engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(query)
            primary_key_columns = cur.fetchall()

    except psycopg.Error as e:
        logger.error(f"Error executing query: {e}")
        raise e

    return [col[0] for col in primary_key_columns]


def get_table_serial_columns(*, engine, table_name: str, schema: str = "public") -> List[str]:
    """Retrieve the name of the column with the specified primary key.

    Args:
        engine: The database engine to use for executing the query.
        table_name: name of the table
        schema: The name of the schema containing the table.

    Returns:
        List[str]: The name of the serial columns in the table.
    """
    # clean the schema
    if schema != "public":
        schema = schema.lower().replace("-", "_").strip()

    # compose the query
    query = sql.SQL(
        """
    SELECT c.column_name
    FROM information_schema.columns c
    JOIN pg_attrdef ad ON ad.adrelid = (c.table_schema || '.' || c.table_name)::regclass
    AND ad.adnum = c.ordinal_position
    WHERE c.table_name = {table_name}
    AND c.table_schema = {schema}
    AND c.column_default LIKE 'nextval%'::text;
    """
    ).format(table_name=sql.Literal(table_name), schema=sql.Literal(schema))

    # launch the query
    try:
        with engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(query)
            serial_columns = cur.fetchall()

    except psycopg.Error as e:
        logger.error(f"Error executing query: {e}")
        raise e

    return [col[0] for col in serial_columns]


def create_query_from_file(
    filename: str,
    folder: Path,
) -> str | None:
    """You can create a query string for SQLAlchemy query launch using a specific `.sql` file.

    This function parse the file, do some transformations and return to you the query string in the correct syntax.

    Be careful: this is a simple function, we have to improve the function with a more sophisticated algorithms to parse the file

    Args:
        filename (str): Name of the file
        folder (str, optional): Path to the file.

    Raises:
        FileNotFoundError: If the file path provided does not exists
        Exception: If the file is empty

    Returns:
        Optional[str]: SQL query found inside the .sql file in a string format
    """
    file_query = os.path.join(folder, filename)

    # check if the file exist
    if not os.path.isfile(file_query):
        message = f"File: {file_query} don't exist, please check the path or the name"
        logger.error(message)
        raise FileNotFoundError(message)

    # check if the file is not empty
    if os.stat(file_query).st_size == 0:
        message = f"Input file: {file_query} is empty"
        logger.error(message)
        raise Exception(message)

    # Create an empty command string
    sql_command: str = ""

    with open(file_query) as sql_file:
        # Iterate over all lines in the sql file
        for line in sql_file:
            # Ignore commented lines
            if not line.startswith("--") or line.strip("\n") or line.startswith("\\*") or line.startswith("*\\"):
                # Append line to the command string
                sql_command += line.strip(" \n ")  # noqa B005

                # If the command string ends with ';', it is a full statement
                if sql_command.endswith(";"):
                    # Try to execute statement and commit it
                    return sql_command[:-1]
                sql_command += " "

    return sql_command
