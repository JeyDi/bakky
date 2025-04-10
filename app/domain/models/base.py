from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, MetaData
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import as_declarative

# Use naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Create a MetaData object with the naming convention
metadata = MetaData(naming_convention=convention)


@as_declarative(metadata=metadata)
class Base:
    """Base class.

    Returns:
        str: Lowercase class name
    """

    id: Any
    __name__: str
    # Generate __tablename__ automatically

    def to_dict(self):
        """Converts the object to a dictionary representation.

        Returns:
            dict: A dictionary containing the object's attributes as key-value pairs.
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def set_schema(cls, schema_name: str):
        """Set the schema name for the class.

        Args:
            schema_name (str): The name of the schema.
        """
        # cls.schema = schema_name
        cls.metadata.schema = schema_name
        for table in cls.metadata.tables.values():
            table.schema = schema_name

    @declared_attr
    def __tablename__(cls) -> str:  # NOQA: N805
        """Get table name.

        Returns:
            str: Table name
        """
        return cls.__name__.lower()


class TimestampMixin:
    """Mixin to add created_at and updated_at columns to models."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
