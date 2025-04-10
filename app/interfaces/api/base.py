"""Base CRUD operations for database models."""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import func, select

from app.domain.models.base import Base
from app.infrastructure.relational.engine import AlchemyEngine

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base class that provides CRUD operations for a SQLAlchemy model.

    Args:
        model: The SQLAlchemy model
    """

    def __init__(self, model: Type[ModelType]):
        """Initialize the CRUD operations with a SQLAlchemy model.

        Args:
            model: The SQLAlchemy model class
        """
        self.model = model

    async def get(*, self, db: AlchemyEngine = AlchemyEngine(), table_id: Any) -> Optional[ModelType]:
        """Get a record by ID.

        Args:
            db: Database session
            id: Record ID

        Returns:
            The record if found, None otherwise
        """
        query = select(self.model).filter(self.model.id == table_id)
        result = await db.engine.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AlchemyEngine = AlchemyEngine(), *, skip: int = 0, limit: int = 100, tenant_id: Optional[int] = None
    ) -> List[ModelType]:
        """Get multiple records with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            tenant_id: Optional tenant ID filter

        Returns:
            List of records
        """
        query = select(self.model)

        # Apply tenant filter if model has tenant_id and tenant_id is provided
        if hasattr(self.model, "tenant_id") and tenant_id is not None:
            query = query.filter(self.model.tenant_id == tenant_id)

        query = query.offset(skip).limit(limit)
        result = await db.engine.execute(query)
        return result.scalars().all()

    async def count(self, db: AlchemyEngine = AlchemyEngine(), tenant_id: Optional[int] = None) -> int:
        """Count total records.

        Args:
            db: Database session
            tenant_id: Optional tenant ID filter

        Returns:
            Total count of records
        """
        query = select(func.count()).select_from(self.model)

        # Apply tenant filter if model has tenant_id and tenant_id is provided
        if hasattr(self.model, "tenant_id") and tenant_id is not None:
            query = query.filter(self.model.tenant_id == tenant_id)

        result = await db.engine.execute(query)
        return result.scalar_one()

    async def create(
        self, db: AlchemyEngine = AlchemyEngine(), *, obj_in: Union[CreateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Create a new record.

        Args:
            db: Database session
            obj_in: Data to create record with

        Returns:
            Created record
        """
        obj_in_data = obj_in.model_dump() if isinstance(obj_in, BaseModel) else obj_in
        db_obj = self.model(**obj_in_data)
        db.engine.add(db_obj)
        await db.engine.commit()
        await db.engine.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AlchemyEngine = AlchemyEngine(), *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update a record.

        Args:
            db: Database session
            db_obj: Database object to update
            obj_in: New data to update with

        Returns:
            Updated record
        """
        obj_data = jsonable_encoder(db_obj)
        update_data = obj_in.model_dump(exclude_unset=True) if isinstance(obj_in, BaseModel) else obj_in

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.engine.add(db_obj)
        await db.engine.commit()
        await db.engine.refresh(db_obj)
        return db_obj

    async def remove(self, db: AlchemyEngine = AlchemyEngine(), *, table_id: int) -> Optional[ModelType]:
        """Delete a record.

        Args:
            db: Database session
            id: Record ID

        Returns:
            Deleted record or None if not found
        """
        obj = await self.get(db=db, id=table_id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def filter_by(
        self,
        db: AlchemyEngine = AlchemyEngine(),
        *,
        skip: int = 0,
        limit: int = 100,
        tenant_id: Optional[int] = None,
        **filters,
    ) -> List[ModelType]:
        """Filter records by specified criteria.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            tenant_id: Optional tenant ID filter
            **filters: Filter criteria

        Returns:
            List of records matching filters
        """
        query = select(self.model)

        # Apply tenant filter
        if hasattr(self.model, "tenant_id") and tenant_id is not None:
            query = query.filter(self.model.tenant_id == tenant_id)

        # Apply other filters
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                column = getattr(self.model, field)

                # Handle different filter types based on value
                if isinstance(value, list):
                    query = query.filter(column.in_(value))
                elif isinstance(value, tuple) and len(value) == 2:
                    # Range filter (min, max)
                    min_val, max_val = value
                    if min_val is not None:
                        query = query.filter(column >= min_val)
                    if max_val is not None:
                        query = query.filter(column <= max_val)
                elif isinstance(value, str) and value.startswith("%") and value.endswith("%"):
                    # LIKE filter
                    query = query.filter(column.ilike(value))
                else:
                    query = query.filter(column == value)

        query = query.offset(skip).limit(limit)
        result = await db.engine.execute(query)
        return result.scalars().all()
