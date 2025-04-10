# noqa: A005
import os
from enum import Enum
from pathlib import Path
from typing import Union

import pandas as pd
import polars as pl

DataframeType = Union[list, dict, pd.DataFrame, pl.DataFrame, pl.LazyFrame]
PathType = Union[str, os.PathLike, Path]


class ExtendedEnum(Enum):
    """Extends the enum class to be able to return the Enum names.

    Args:
        Enum (Enum): Extends Enum type
    """

    @classmethod
    def options(cls) -> str:
        """Get the enum values a semicolon separated string.

        Returns:
            str: Semicolon separated enums
        """
        return "; ".join([str(type(e).__name__) + "." + e.name for e in cls])

    @classmethod
    def list_options(cls) -> list:
        """Get the enum values as a list of strings.

        Returns:
            list: List of enum values
        """
        return list(cls.__members__.keys())

    @classmethod
    def set_options(cls) -> set:
        """Get the enum values as a set of strings.

        Best performance to test if value in set of options.

        Returns:
            set: List of enum values
        """
        return set(cls)


class DataType(ExtendedEnum):
    """Enum for the return type of DC functions.

    - DataType.LIST -> return a list.
    - DataType.DICT -> return a dict.
    - DataType.PANDAS -> return a Pandas DataFrame.
    - DataType.POLARS -> return a Polars DataFrame.
    - DataType.LAZY_POLARS -> return a Polars LazyFrame.
    """

    LIST = 1
    DICT = 2
    PANDAS = 3
    POLARS = 4
    LAZY_POLARS = 5
    DUCKDB = 6
    ARROW = 7
    TUPLE = 8


class FileFormat(ExtendedEnum):
    """Enum for the return type of DC functions.

    - FileFormat.PARQUET -> read or write a Parquet file.
    - FileFormat.FEATHER -> read or write a Feather file.
    - FileFormat.CSV -> read or write a CSV file.
    - FileFormat.JSON -> read or write a JSON file.
    - FileFormat.YAML -> read or write a YAML file.
    - FileFormat.ORC -> read or write an ORC file.
    - FileFormat.PARQUET_DATASET -> read or write a Parquet Dataset (Deprecated).

    """

    PARQUET = 1
    FEATHER = 2
    CSV = 3
    JSON = 4
    YAML = 5
    ORC = 6
