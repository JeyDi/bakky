import pandas as pd
import polars as pl
import psycopg
from loguru import logger
from psycopg import sql
from psycopg.rows import dict_row

from app.domain.schemas.types import DataType
from app.infrastructure.relational.engine import DBEngine
from app.infrastructure.relational.utils import (
    get_primary_key_columns,
    get_table_serial_columns,
    psycopg_connection_string,
)


def build_conflicts_query(unique_columns: list[str], columns: list[str], optional_updates: dict | None = None) -> str:
    """Build the ON CONFLICT clause for a query based on the unique columns and the columns to update.

    Args:
        unique_columns (list[str]): A list of column names that should have unique values.
        columns (list[str]): A list of column names to update in case of conflict.
        optional_updates (dict, optional): A dictionary containing the column-value pairs to update. Defaults to None.

    Returns:
        str: The ON CONFLICT clause for the query.
    """
    unique_columns_str = ", ".join(unique_columns)
    if optional_updates is None:
        update_statements = ", ".join([f"{col}=EXCLUDED.{col}" for col in columns if col not in unique_columns])
    else:
        update_statements: str = ", ".join([f"{col}={value}" for col, value in optional_updates.items()])
    return f"ON CONFLICT ({unique_columns_str}) DO UPDATE SET {update_statements}"


def insert_data(
    *,
    engine: DBEngine = DBEngine(),
    data: dict | pl.DataFrame | pd.DataFrame | list,
    table_name: str,
    data_type: DataType = DataType.POLARS,
    unique_columns: str | list | None = None,
    optional_updates: dict | None = None,
) -> bool:
    """Insert data into a PostgreSQL table from different format.

    You can pass different data types to be inserted into the table. The function will handle the conversion and insertion.
    Supported data types are:
    - Python Dictionary
    - Polars DataFrame
    - Pandas DataFrame

    If you pass unique_columns, the function will handle the conflict resolution in case of unique constraint violation.
    The logic is to update the existing row with the new values.

    Args:
        engine (DBEngine): The database engine to use. Defaults to DBEngine().
        data (dict | pl.DataFrame | pd.DataFrame): The data to be inserted. It can be a dictionary, a Polars DataFrame, or a Pandas DataFrame.
        table_name (str): The name of the table to insert the data into. You can use also the schema (satellite_name.table_name).
        data_type (DataType, optional): The type of the data. Defaults to DataType.POLARS.
        unique_columns (str, list, optional): A list of column names that should have unique values. Defaults to None.
        optional_updates (dict, optional): A dictionary containing the column-value pairs to update in case of conflict. Defaults to None.

    Returns:
        bool: True if the data was inserted successfully, False otherwise.
    """
    if data_type not in DataType.set_options():
        raise TypeError(f"Unknown data type {data_type}. data_type should be one of {DataType.options()}")

    if isinstance(unique_columns, str):
        unique_columns = [unique_columns]

    insert_statement = "INSERT INTO %s " % table_name

    # Python Dictionary Data
    if data_type == DataType.DICT and isinstance(data, (list, dict)):
        # Assuming `data` is a list of dictionaries where each dictionary represents a row
        if not data or not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
            logger.error("Data must be a list of dictionaries for DataType.DICT")
            return False

        # Extract column names from the first dictionary (assuming all dictionaries have the same keys)
        columns = data[0].keys()
        column_names = ", ".join(list(columns))
        placeholders = ", ".join(["%s"] * len(columns))

        insert_query = f"{insert_statement} ({column_names}) VALUES ({placeholders})"

        if unique_columns and len(unique_columns) > 0:
            insert_query += build_conflicts_query(unique_columns, columns, optional_updates)

        # Convert each dictionary to a tuple of values
        values = [tuple(row[col] for col in columns) for row in data]

        with engine.connect() as conn:
            try:
                cur = conn.cursor()
                with conn.transaction():
                    cur.executemany(insert_query, values)
                    logger.debug("Query executed and data inserted correctly")
                    return True
            except psycopg.Error as e:
                logger.error(f"Error executing query: {e}")
                conn.rollback()
                return False

    # POLARS Dataframe
    elif data_type == DataType.POLARS and isinstance(data, pl.DataFrame):
        # Extract column names from the DataFrame
        columns = data.columns

        # Validate and map column types
        # TODO: Implement the type checking with the table like SQLAlchemy
        # type_mapping = polars_sql_mapping()
        # insert_columns = []
        # for column_name, column_type in zip(data.columns, data.dtypes, strict=False):
        #     sql_type = type_mapping.get(type(column_type), None)
        #     if not sql_type:
        #         logger.error(f"Unsupported column type for {column_name}: {column_type}")
        #         return False
        #     insert_columns.append((column_name, sql_type))

        column_names = ", ".join(list(columns))
        values = ", ".join(["%s"] * len(columns))

        insert_query = f"{insert_statement} ({column_names}) VALUES ({values})"

        # Manage the Unique conflicts
        # Check if unique_columns is provided and not empty
        if unique_columns and len(unique_columns) > 0:
            insert_query += build_conflicts_query(unique_columns, columns, optional_updates)

        # Convert the Polars DataFrame to a list of tuples
        values = [tuple(row) for row in data.to_numpy()]

        with engine.connect() as conn:
            try:
                cur = conn.cursor()
                with conn.transaction():
                    cur.executemany(insert_query, values)
                    logger.debug("Query executed and data inserted correctly")
                    return True
            except psycopg.Error as e:
                logger.error(f"Error executing query: {e}")
                conn.rollback()
                return False

    # PANDAS Dataframe
    elif data_type == DataType.PANDAS and isinstance(data, pd.DataFrame):
        columns = data.columns

        # Prepare the base insert query
        insert_query = f"{insert_statement} ({', '.join(columns)}) VALUES ({', '.join(['%s' for _ in columns])})"

        # Handle unique conflicts if unique_columns is provided
        if unique_columns and len(unique_columns) > 0:
            insert_query += build_conflicts_query(unique_columns, columns, optional_updates)

        # Convert the Pandas DataFrame to a list of tuples
        values = [tuple(row) for row in data[columns].to_numpy()]

        with engine.connect() as conn:
            try:
                cur = conn.cursor()
                with conn.transaction():
                    cur.executemany(insert_query, values)
                    logger.debug("Query executed and data inserted correctly")
                    return True
            except psycopg.Error as e:
                logger.error(f"Error executing query: {e}")
                conn.rollback()
                return False

    logger.error(f"Data type {data_type} not supported for this import operation")
    return False


def read_data(
    *,
    engine: DBEngine = DBEngine(),
    query: str,
    return_type: DataType = DataType.POLARS,
) -> pl.LazyFrame | pl.DataFrame | pd.DataFrame | dict | list | None:
    """Reads data from a PostgreSQL database using the specified query and returns the result in the specified format.

    Args:
        engine (DBEngine | None, optional): The database engine to use for the connection. Defaults to DBEngine().
        query (str): The SQL query to execute.
        return_type (DataType, optional): The desired format of the returned data. Defaults to DataType.POLARS.

    Returns:
        pl.DataFrame | pd.DataFrame | dict | None: The result of the query in the specified format, or None if an error occurred.

    Raises:
        TypeError: If the specified return_type is not one of the supported data types.
        Exception: If an error occurs while executing the query.

    """
    if return_type not in DataType.set_options():
        raise TypeError(f"Unknown data type {return_type}. data_type should be one of {DataType.options()}")

    # Compose the query string
    engine_string = psycopg_connection_string()

    try:
        # Polars
        if return_type in (DataType.POLARS, DataType.LAZY_POLARS, DataType.ARROW):
            df = pl.read_database_uri(uri=engine_string, query=query, engine="connectorx")

            if return_type == DataType.LAZY_POLARS:
                return df.lazy()

            if return_type == DataType.POLARS:
                return df

            if return_type == DataType.ARROW:
                return df.to_arrow()

        # Pandas
        elif return_type == DataType.PANDAS:
            with engine.connect() as conn:
                return pd.read_sql(sql=query, con=conn)

        # Dict
        elif return_type == DataType.DICT:
            with engine.connect() as conn:
                cur = conn.cursor(row_factory=dict_row)
                return cur.execute(query).fetchall()

        # Tuple (standard psycopg return)
        elif return_type == DataType.TUPLE:
            with engine.connect() as conn:
                cur = conn.cursor()
                return cur.execute(query).fetchall()

        logger.exception(f"Return type {return_type} not supported for this read operation")
        return None
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        logger.exception(e)
        raise


def delete_data(
    *,
    engine: DBEngine = DBEngine(),
    table_name: str,
    condition_dict: dict[str, list] | dict[str, str],
) -> int:
    """Delete rows from a database table based on the given conditions.

    Args:
        engine (DBEngine | None, optional): The database engine to use for the connection. Defaults to DBEngine().
        table_name (str): The name of the table to delete rows from. You can use also the schema (db_schema.table_name). By default the schema is: public.
        condition_dict (dict[str:list] | dict[str:str]): A dictionary specifying the conditions for deletion.
            The keys represent the column names, and the values can be either a list of values or a single value.

    Returns:
        int: The number of rows deleted.

    Raises:
        psycopg.Error: If an error occurs while executing the delete query.
    """
    conditions = []
    values = []

    # check the schema
    if "." in table_name:
        schema_name, table_name = table_name.split(".", 1)
    else:
        schema_name = "public"

    for column, val in condition_dict.items():
        if isinstance(val, list):
            placeholders = ", ".join(["%s"] * len(val))
            conditions.append(f"{column} IN ({placeholders})")
            values.extend(val)
        else:
            conditions.append(f"{column} = %s")
            values.append(val)

    delete_query = sql.SQL("DELETE FROM {schema}.{table} WHERE {conditions}").format(
        schema=sql.Identifier(schema_name),
        table=sql.Identifier(table_name),
        conditions=sql.SQL(" AND ".join(conditions)),
    )
    with engine.connect() as conn:
        try:
            cur = conn.cursor()
            cur.execute(delete_query, values)
            return cur.rowcount
        except psycopg.Error as e:
            logger.error(f"Error executing query: {e}")
            conn.rollback()
            return 0


def update_data(
    *,
    engine: DBEngine | None = DBEngine(),
    table_name: str,
    update_dict: dict[str, str],
    condition_dict: dict[str, str],
) -> int | None:
    """Update data in the specified table based on the given update and condition dictionaries.

    Args:
        engine (DBEngine | None, optional): The database engine to use. Defaults to DBEngine().
        table_name (str): The name of the table to update.
        update_dict (dict[str:str]): A dictionary containing the column-value pairs to update.
        condition_dict (dict[str:str]): A dictionary containing the column-value pairs to use as conditions for the update.

    Returns:
        int | None: The number of rows affected by the update, or None if an error occurred.

    Raises:
        psycopg.Error: If an error occurs while executing the update query.
    """
    update_statement = f"UPDATE {table_name} SET "  # noqa

    update_columns = []
    for column, _ in update_dict.items():  # noqa
        update_columns.append(f"{column} = %s")

    update_query = update_statement + ", ".join(update_columns)

    conditions = []
    for column, _ in condition_dict.items():  # noqa
        conditions.append(f"{column} = %s")

    update_query += f" WHERE {' AND '.join(conditions)}"
    with engine.connect() as conn:
        try:
            cur = conn.cursor()
            cur.execute(update_query, list(update_dict.values()) + list(condition_dict.values()))
            return cur.rowcount
        except psycopg.Error as e:
            logger.error(f"Error executing query: {e}")
            conn.rollback()
            return None


def upsert_data(
    *,
    engine: DBEngine = DBEngine(),
    table_name: str,
    data: dict | pl.DataFrame | pd.DataFrame,
    data_type: DataType = DataType.POLARS,
    unique_columns: str | list | None = None,
    force_update: bool = True,
) -> bool:
    """Insert or update the data inside a Postgres SQL table using multiple data types and conflict resolution.

    Be careful this function it's iterating row by row instead executing everything in a block of data.
    It's slower than the insert_data function, but it's safer for the unique constraints and multiple insert and update.

    Main idea:
    - Insert the data into the table
    - If there is a conflict with the unique columns and you force_update, update the row with the new values
        - if the update it's not working also the function will return False

    This function will work also if you don't specific the serial or bigserial columns or keys in the unique_columns, automatically will update or insert the new row.

    Args:
        engine (DBEngine | None, optional): The database engine to use for the connection. Defaults to DBEngine().
        table_name (str): The name of the table to delete rows from. You can use also the schema (db_schema.table_name). By default the schema is: public.
        data (dict | pl.DataFrame | pd.DataFrame): The data to be inserted. It can be a dictionary, a Polars DataFrame, or a Pandas DataFrame.
        data_type (DataType, optional): The type of the data. Defaults to DataType.POLARS.
        unique_columns (str | list, optional): A list of column names that should have unique values. Defaults to None.
        force_update (bool, optional): If True, perform an update on conflict. Defaults to False.

    Returns:
        bool: True if the data was inserted or updated successfully, False otherwise.
    """
    insert_data: dict = {}
    if isinstance(data, pd.DataFrame) and data.empty or isinstance(data, pl.DataFrame) and data.is_empty():
        raise ValueError("Input data object is empty or not valid")

    if not isinstance(data, (pl.DataFrame, pd.DataFrame)) and not data:
        raise ValueError("Input data object is empty or not valid")

    if data_type == DataType.DICT and isinstance(data, (list, dict)):
        # Assuming `data` is a list of dictionaries where each dictionary represents a row
        if not data or not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
            logger.error("Data must be a list of dictionaries for DataType.DICT")
            return False

        insert_data = data

    elif data_type == DataType.POLARS and isinstance(data, pl.DataFrame):
        insert_data = data.to_dict()
    elif data_type == DataType.PANDAS and isinstance(data, pd.DataFrame):
        insert_data = data.to_dicts(orient="records")

    else:
        logger.error(f"Data type {data_type} not supported for this import operation")
        raise Exception(f"Data type {data_type} not supported for this import operation")

    # Convert unique_columns to a list if it's a string and force to list if it's None
    if isinstance(unique_columns, str):
        unique_columns = [unique_columns]
    if unique_columns is None:
        unique_columns = []

    # check if table_name contains the schema
    if "." in table_name:
        schema_name, table_name = table_name.split(".", 1)
    else:
        schema_name = "public"

    original_unique_columns = unique_columns

    if len(unique_columns) == 0:
        # unique columns will consider the primary key columns
        unique_columns = get_primary_key_columns(engine=engine, table_name=table_name, schema=schema_name)

    serial_columns = get_table_serial_columns(engine=engine, table_name=table_name, schema=schema_name)

    try:
        with engine.connect() as conn:
            cur = conn.cursor()
            for row in insert_data:
                # Extract columns from the data
                columns = list(row.keys())
                # Create the update set, excluding unique columns
                update_assignments = ", ".join(
                    [f"{col} = EXCLUDED.{col}" for col in columns if col not in unique_columns]
                )

                # Check if all unique_columns are present in the data
                if len(original_unique_columns) > 0:
                    for col in original_unique_columns:
                        if col not in columns:
                            logger.error(f"Unique column '{col}' not found in the data")
                            return False

                # Check if serial columns are in the row data
                # serial_columns_in_row = [col for col in serial_columns if col in row]
                serial_columns_not_in_row = [col for col in serial_columns if col not in row]

                # Reset the serial keys for each serial column
                for serial_column in serial_columns:
                    cur.execute(
                        f"SELECT setval(pg_get_serial_sequence('{schema_name}.{table_name}', '{serial_column}'), (SELECT COALESCE(MAX({serial_column}), 0) FROM {schema_name}.{table_name}) + 1);"  # noqa
                    )

                # Create the insert query
                insert_query = f"""
                INSERT INTO {schema_name}.{table_name} ({", ".join(columns)})
                VALUES ({", ".join(["%s" for _ in columns])})
                ON CONFLICT DO NOTHING
                RETURNING *;
                """  # noqa
                values_list = [row[col] for col in columns]
                try:
                    results = cur.execute(insert_query, values_list).fetchall()
                    if results is None or len(results) == 0:
                        raise psycopg.Error("unique constraint violation")
                except psycopg.Error as e:
                    if "unique constraint" in str(e):
                        if force_update:
                            # Create the update query
                            update_query = f"""
                            INSERT INTO {schema_name}.{table_name} ({", ".join(columns + serial_columns_not_in_row)})
                            VALUES ({", ".join(["%s" for _ in columns] + ["DEFAULT" for _ in serial_columns_not_in_row])})
                            ON CONFLICT ({", ".join(unique_columns)})
                            DO UPDATE SET {update_assignments};
                            """  # noqa
                            try:
                                cur.execute(update_query, values_list)
                            except psycopg.Error as update_error:
                                logger.error(f"Error executing update query: {update_error}")
                                conn.rollback()
                                return False
                        else:
                            logger.error(f"Unique constraint violation: {e}")
                            conn.rollback()
                            return False
                    else:
                        logger.error(f"Error executing insert query: {e}")
                        conn.rollback()
                        return False
            conn.commit()
            return True
    except psycopg.Error as e:
        logger.error(f"Error connecting to the database: {e}")
        return False
