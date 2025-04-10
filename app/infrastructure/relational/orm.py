# database manager functions to interact with database
# based on SQLAlalchemy ORM management (for objects and not for queries)
from loguru import logger
from sqlalchemy import MetaData, inspect, text
from sqlalchemy.engine import Engine

from app.domain.models import base
from app.infrastructure.relational.engine import AlchemyEngine


def create_tables(engine: Engine = AlchemyEngine, schema_name: str | None = None) -> bool:
    """Create all the tables defined as python class with SQAlchemy inside the project.

    Args:
        engine (Engine): The connection engine where you want to execute the query.

    Raises:
        Exception: If it's impossible to create the tables.

    Returns:
        result (bool): True if the tables are created, False otherwise.
    """
    try:
        if schema_name is not None:
            with engine.connect() as connection:
                connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                connection.commit()

            base.Base.set_schema(schema_name)

        # Create the tables
        base.Base.metadata.create_all(engine)

        logger.debug("Tables created successfully")
        return True
    except Exception as message:
        logger.error("fImpossible to create the tables: {message}")
        logger.exception(message)
        raise Exception(message) from message


def drop_tables(engine: Engine = AlchemyEngine, confirm: bool = False, schema_name: str | None = None) -> bool:
    """Drop all the tables inside a database.

    Args:
        engine (Engine): The connection engine where you want to execute the query.
        confirm (bool): Safe confirmation flag to drop all the tables as "security" measure.
        schema_name (str): The schema name where you want to drop the tables.

    Returns:
        result (bool): True if the tables are dropped, False otherwise.
    """
    try:
        if confirm:
            if schema_name is not None:
                base.Base.set_schema(schema_name)

            # Drop the tables
            base.Base.metadata.drop_all(bind=engine)

            return True
        return False
    except Exception as message:
        logger.error("Impossible to drop all the tables in the db")
        logger.exception(message)
        raise Exception(message) from message


def check_table(*, engine: Engine = AlchemyEngine, table_name: str = "", schema: str = "public") -> list:
    """Check if there are some tables in the database.

    You can also use a table names to check if the table name exist.

    Args:
        engine (Engine): The connection engine where you want to execute the query.
        table_name (str): If you want to search a specific table. Default is empty string.
        schema (str): The schema in which to check for tables. Default is 'public'.

    Raises:
        Exception: if it's impossible to retrieve the list of the tables.

    Returns:
        result (list): List of the tables in the database.
    """
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema=schema)
        if tables:
            if table_name:
                return [x for x in tables if table_name.lower() == x.lower()]
            return tables
        logger.info("No tables existing in the schema '%s'", schema)
        return []
    except Exception as message:
        logger.error("Impossible to get the table names in the schema '%s'", schema)
        logger.exception(message)
        raise Exception(message) from message


def get_table_schema(*, engine: Engine = AlchemyEngine, table_name: str, schema_name: str = "public") -> dict:
    """Get the table schema from the database using sqlalchemy metadata reflection.

    If you want more information, refer to the official sqlalchemy documentation:
    - https://docs.sqlalchemy.org/en/14/core/reflection.html#reflecting-all-tables-at-once.

    Args:
        engine (sqlalchemy.engine): the connection engine where you want to execute the query.
        table_name (str): the tablename you want to get the schema.
        schema_name (str): the schema name where the table is located.

    Raises:
        Exception: if it's impossible to get the table schema for that table.

    Returns:
        result (dict): The table schema as a dict.
    """
    try:
        # Use SQLAlchemy metadata reflection with the specified schema
        metadata = MetaData(schema=schema_name)
        metadata.reflect(bind=engine, only=[table_name])
        table_schema = {}
        table = metadata.tables.get(f"{schema_name}.{table_name}")
        if table:
            for column in table.c:
                table_schema[column.name] = str(column.type)
            return table_schema
        logger.info(f"No columns existing in the table: {table_name} in schema: {schema_name}")
        return {}
    except Exception as message:
        logger.error(f"Impossible to get the schema for the table: {table_name}")
        logger.exception(message)
        raise Exception(message) from message


def insert_data(*, engine: Engine = AlchemyEngine, schema_name: str = "public", data_object: object) -> bool:
    """Insert new data inside a table.

    Since it's an ORM the data_object is a python object that you want to insert inside the database.

    Args:
        engine (Engine): The connection engine where you want to execute the query.
        schema_name (str): The schema name where you want to insert the data.
        data_object (object): Your object you want to insert.

    Raises:
        Exception: if it's impossible to insert the data.

    Returns:
        result (bool): True if the data is inserted, False otherwise.
    """
    try:
        session_local = engine.session
        with session_local.begin() as session:
            # Set the schema for the data object if applicable
            if hasattr(data_object, "__table__"):
                data_object.__table__.schema = schema_name

            # Add the new data
            session.add(data_object)
            session.commit()
            session.refresh(data_object)
        return True
    except Exception as message:
        logger.error(
            f"Impossible to create the table for the object: {data_object.__class__.__name__} in schema: {schema_name}"
        )
        logger.exception(message)
        raise Exception(message) from message


def refresh_data(*, engine: Engine = AlchemyEngine, schema_name: str = "public", data_object: object) -> bool:
    """Refresh the data inside the database for a specific table (object).

    Args:
        engine (Engine): The connection engine where you want to execute the query.
        schema_name (str): The schema name where you want to refresh the data.
        data_object (object): Your object you want to refresh.

    Raises:
        Exception: if it's impossible to refresh the data.

    Returns:
        result (bool): True if the data is refreshed, False otherwise.
    """
    try:
        session_local = engine.session
        with session_local.begin() as session:
            # Set the schema for the data object if applicable
            if hasattr(data_object, "__table__"):
                data_object.__table__.schema = schema_name

            # Refresh the data
            session.refresh(data_object)
        return True
    except Exception as message:
        logger.error(f"Impossible to refresh the object: {data_object.__class__.__name__} in schema: {schema_name}")
        logger.exception(message)
        raise Exception(message) from message


def delete_data(*, engine: Engine = AlchemyEngine, schema_name: str = "public", data_object: object) -> bool:
    """Delete an object from the database. In this case remove a specific table from the db.

    Args:
        engine (Engine): The connection engine where you want to execute the query.
        schema_name (str): The schema name where you want to delete the object.
        data_object (object): Your object you want to delete.

    Raises:
        Exception: if it's impossible to delete the object.

    Returns:
        result (bool): True if the object is deleted, False otherwise.
    """
    try:
        session_local = engine.session
        with session_local.begin() as session:
            # Set the schema for the data object if applicable
            if hasattr(data_object, "__table__"):
                data_object.__table__.schema = schema_name

            # Delete the data
            session.delete(data_object)
            session.commit()
        return True
    except Exception as message:
        logger.error(f"Impossible to delete your object: {data_object.__class__.__name__}")
        logger.exception(message)
        raise Exception(message) from message


def get_data(
    *,
    engine: Engine = AlchemyEngine,
    schema_name: str = "public",
    data_object: object,
    to_dict: bool = False,
    filter_dict: dict = None,
) -> list:
    """Get data from a table with optional filtering.

    Args:
        engine (Engine): The connection engine where you want to execute the query.
        schema_name (str): The schema name where you want to get the data.
        data_object (object): The SQLAlchemy model class representing the table.
        to_dict (bool): Flag to determine if the output should be a list of dictionaries.
        filter_dict (dict): Dictionary containing the filter conditions for the query.

    Returns:
        result (list): List of records in the table, either as objects or dictionaries.
    """
    try:
        session_local = engine.session
        with session_local.begin() as session:
            # Set the schema for the data object if applicable
            if hasattr(data_object, "__table__"):
                data_object.__table__.schema = schema_name

            query = session.query(data_object)

            # Apply filters if filter_dict is provided
            if filter_dict:
                for key, value in filter_dict.items():
                    query = query.filter(getattr(data_object, key) == value)

            results = query.all()

            if to_dict:
                results = [result.to_dict() for result in results]
                # Remove the SQLAlchemy instance state from the dictionary
                for result in results:
                    result.pop("_sa_instance_state", None)

            return results
    except Exception as message:
        logger.error(f"Impossible to retrieve data from table: {data_object.__tablename__}, with schema: {schema_name}")
        logger.exception(message)
        raise Exception(message) from message


def update_data(*, engine: Engine = AlchemyEngine, schema_name: str = "public", update_object: object) -> bool:
    """Update a specific record in a table using an existing object.

    The primary key of the record must be present in the object in order to update it.

    Args:
        engine (Engine): The connection engine where you want to execute the query.
        schema_name (str): The schema name where the table is located.
        update_object (object): An object containing the model class and the fields to update and their new values.

    Returns:
        bool: True if the record was updated successfully, False otherwise.
    """
    try:
        session_local = engine.session
        with session_local.begin() as session:
            # Retrieve the model class from the update_object
            model_class = update_object.__class__

            # Set the schema for the model class if applicable
            if hasattr(model_class, "__table__"):
                model_class.__table__.schema = schema_name

            # Retrieve the primary key attribute name
            primary_key_attr = model_class.__mapper__.primary_key[0].name

            # Retrieve the primary key value from the update_object
            primary_key_value = getattr(update_object, primary_key_attr)

            # Retrieve the record
            record = session.query(model_class).get(primary_key_value)
            if not record:
                logger.error(
                    f"Record with ID {primary_key_value} not found in table {model_class.__tablename__} with schema {schema_name}"
                )
                return False

            # Update the record with the new values
            for key, value in update_object.__dict__.items():
                if key != "_sa_instance_state":
                    setattr(record, key, value)

            session.commit()
            return True
    except Exception as message:
        logger.error(
            f"Impossible to update the record in table: {model_class.__tablename__}, with schema: {schema_name}"
        )
        logger.exception(message)
        raise Exception(message) from message


def update_data_dict(
    *, engine: Engine = AlchemyEngine, schema_name: str = "public", model_class: object, update_dict: dict
) -> bool:
    """Update a specific record in a table using a dictionary as input.

    Inside the update_dict dictionary you need to put also the primary key value to update the record.

    Args:
        engine (Engine): The connection engine where you want to execute the query.
        schema_name (str): The schema name where the table is located.
        model_class (object): The SQLAlchemy model class representing the table.
        update_dict (dict): A dictionary containing the fields to update and their new values.

    Returns:
        bool: True if the record was updated successfully, False otherwise.
    """
    try:
        session_local = engine.session
        with session_local.begin() as session:
            # Set the schema for the model class if applicable
            if hasattr(model_class, "__table__"):
                model_class.__table__.schema = schema_name

            # Retrieve the primary key attribute name
            primary_key_attr = model_class.__mapper__.primary_key[0].name

            # Retrieve the primary key value from the update_data
            primary_key_value = update_data.get(primary_key_attr)
            if primary_key_value is None:
                logger.error(f"Primary key {primary_key_attr} not found in update_data")
                return False

            # Retrieve the record
            record = session.query(model_class).get(primary_key_value)
            if not record:
                logger.error(f"Record with ID {primary_key_value} not found in table {model_class.__tablename__}")
                return False

            # Update the record with the new values
            for key, value in update_dict.items():
                setattr(record, key, value)

            session.commit()
            return True
    except Exception as message:
        logger.error(f"Impossible to update record with ID {primary_key_value} in table {model_class.__tablename__}")
        logger.exception(message)
        raise Exception(message) from message


def delete_record(
    *, engine: Engine = AlchemyEngine, schema_name: str = "public", model_class: object, record_id: int
) -> bool:
    """Delete a specific record from a table.

    Args:
        engine (Engine): The connection engine where you want to execute the query.
        schema_name (str): The schema name where the table is located.
        model_class (object): The SQLAlchemy model class representing the table.
        record_id (int): The ID of the record to delete.

    Returns:
        bool: True if the record was deleted successfully, False otherwise.
    """
    try:
        session_local = engine.session
        with session_local.begin() as session:
            # Set the schema for the model class if applicable
            if hasattr(model_class, "__table__"):
                model_class.__table__.schema = schema_name

            # Retrieve the record
            record = session.query(model_class).get(record_id)

            if not record:
                logger.error(f"Record with ID {record_id} not found in table {model_class.__tablename__}")
                return False

            # Delete the record
            session.delete(record)

            # Commit the changes
            session.commit()
            return True
    except Exception as message:
        logger.error(f"Impossible to delete record with ID {record_id} in table {model_class.__tablename__}")
        logger.exception(message)
        raise Exception(message) from message
