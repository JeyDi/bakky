import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from bson import ObjectId
from loguru import logger
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.infrastructure.mongo.engine import MongoDBEngine


class MongoEncoder(json.JSONEncoder):
    """Custom JSON encoder for MongoDB data types."""

    def default(self, obj):
        """Override default method to handle ObjectId and datetime serialization."""
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


class MongoDBData:
    """A data layer for MongoDB that provides CRUD operations."""

    def __init__(self, engine: MongoDBEngine = MongoDBEngine()):
        """Initialize the MongoDB data layer.

        Args:
            engine: MongoDBEngine instance
        """
        self.engine = engine

    def get_collection(self, collection_name: str) -> Collection:
        """Get a MongoDB collection.

        Args:
            collection_name: Name of the collection

        Returns:
            MongoDB collection object
        """
        return self.engine.get_collection(collection_name)

    def insert_one(self, collection_name: str, document: Dict) -> Optional[str]:
        """Insert a single document into a collection.

        Args:
            collection_name: Name of the collection
            document: Document to insert

        Returns:
            ID of the inserted document or None if insertion failed
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.insert_one(document)
            logger.info(f"Inserted document in {collection_name} with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Failed to insert document in {collection_name}: {e}")
            return None

    def insert_many(self, collection_name: str, documents: List[Dict]) -> Optional[List[str]]:
        """Insert multiple documents into a collection.

        Args:
            collection_name: Name of the collection
            documents: List of documents to insert

        Returns:
            List of inserted document IDs or None if insertion failed
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.insert_many(documents)
            inserted_ids = [str(id) for id in result.inserted_ids]  # noqa
            logger.info(f"Inserted {len(inserted_ids)} documents in {collection_name}")
            return inserted_ids
        except PyMongoError as e:
            logger.error(f"Failed to insert documents in {collection_name}: {e}")
            return None

    def find_one(self, collection_name: str, query: Dict) -> Optional[Dict]:
        """Find a single document in a collection.

        Args:
            collection_name: Name of the collection
            query: Query to filter documents

        Returns:
            Document or None if not found
        """
        try:
            collection = self.get_collection(collection_name)
            document = collection.find_one(query)
            if document:
                return json.loads(json.dumps(document, cls=MongoEncoder))
            return None
        except PyMongoError as e:
            logger.error(f"Failed to find document in {collection_name}: {e}")
            return None

    def find_by_id(self, collection_name: str, document_id: str) -> Optional[Dict]:
        """Find a document by its ID.

        Args:
            collection_name: Name of the collection
            document_id: ID of the document to find

        Returns:
            Document or None if not found
        """
        try:
            object_id = ObjectId(document_id)
            return self.find_one(collection_name, {"_id": object_id})
        except Exception as e:
            logger.error(f"Failed to find document by ID in {collection_name}: {e}")
            return None

    def find(
        self,
        collection_name: str,
        query: Dict = None,
        sort: List[Tuple[str, int]] = None,
        limit: int = 0,
        skip: int = 0,
    ) -> List[Dict]:
        """Find documents in a collection.

        Args:
            collection_name: Name of the collection
            query: Query to filter documents (default: {})
            sort: List of (field, direction) tuples for sorting (default: None)
            limit: Maximum number of documents to return (default: 0 = no limit)
            skip: Number of documents to skip (default: 0)

        Returns:
            List of documents
        """
        query = query or {}
        try:
            collection = self.get_collection(collection_name)
            cursor = collection.find(query)

            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)

            results = list(cursor)
            return json.loads(json.dumps(results, cls=MongoEncoder))
        except PyMongoError as e:
            logger.error(f"Failed to find documents in {collection_name}: {e}")
            return []

    def update_one(self, collection_name: str, query: Dict, update: Dict, upsert: bool = False) -> Optional[Dict]:
        """Update a single document in a collection.

        Args:
            collection_name: Name of the collection
            query: Query to find the document to update
            update: Update operations to apply
            upsert: Whether to insert if document doesn't exist (default: False)

        Returns:
            Dict with modified_count, matched_count, and upserted_id if successful,
            None otherwise
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.update_one(query, update, upsert=upsert)

            response = {
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": str(result.upserted_id) if result.upserted_id else None,
            }

            logger.info(f"Updated document in {collection_name}: {response}")
            return response
        except PyMongoError as e:
            logger.error(f"Failed to update document in {collection_name}: {e}")
            return None

    def update_by_id(self, collection_name: str, document_id: str, update: Dict) -> Optional[Dict]:
        """Update a document by its ID.

        Args:
            collection_name: Name of the collection
            document_id: ID of the document to update
            update: Update operations to apply

        Returns:
            Dict with modified_count and matched_count if successful, None otherwise
        """
        try:
            object_id = ObjectId(document_id)
            return self.update_one(collection_name, {"_id": object_id}, update)
        except Exception as e:
            logger.error(f"Failed to update document by ID in {collection_name}: {e}")
            return None

    def update_many(self, collection_name: str, query: Dict, update: Dict) -> Optional[Dict]:
        """Update multiple documents in a collection.

        Args:
            collection_name: Name of the collection
            query: Query to find documents to update
            update: Update operations to apply

        Returns:
            Dict with modified_count and matched_count if successful, None otherwise
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.update_many(query, update)

            response = {"matched_count": result.matched_count, "modified_count": result.modified_count}

            logger.info(f"Updated {result.modified_count} documents in {collection_name}")
            return response
        except PyMongoError as e:
            logger.error(f"Failed to update documents in {collection_name}: {e}")
            return None

    def delete_one(self, collection_name: str, query: Dict) -> Optional[int]:
        """Delete a single document from a collection.

        Args:
            collection_name: Name of the collection
            query: Query to find the document to delete

        Returns:
            Number of documents deleted (0 or 1) or None if deletion failed
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.delete_one(query)

            logger.info(f"Deleted {result.deleted_count} document from {collection_name}")
            return result.deleted_count
        except PyMongoError as e:
            logger.error(f"Failed to delete document from {collection_name}: {e}")
            return None

    def delete_by_id(self, collection_name: str, document_id: str) -> Optional[int]:
        """Delete a document by its ID.

        Args:
            collection_name: Name of the collection
            document_id: ID of the document to delete

        Returns:
            Number of documents deleted (0 or 1) or None if deletion failed
        """
        try:
            object_id = ObjectId(document_id)
            return self.delete_one(collection_name, {"_id": object_id})
        except Exception as e:
            logger.error(f"Failed to delete document by ID from {collection_name}: {e}")
            return None

    def delete_many(self, collection_name: str, query: Dict) -> Optional[int]:
        """Delete multiple documents from a collection.

        Args:
            collection_name: Name of the collection
            query: Query to find documents to delete

        Returns:
            Number of documents deleted or None if deletion failed
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.delete_many(query)

            logger.info(f"Deleted {result.deleted_count} documents from {collection_name}")
            return result.deleted_count
        except PyMongoError as e:
            logger.error(f"Failed to delete documents from {collection_name}: {e}")
            return None

    def count(self, collection_name: str, query: Dict = None) -> Optional[int]:
        """Count documents in a collection.

        Args:
            collection_name: Name of the collection
            query: Query to filter documents (default: {})

        Returns:
            Number of documents or None if count failed
        """
        query = query or {}
        try:
            collection = self.get_collection(collection_name)
            return collection.count_documents(query)
        except PyMongoError as e:
            logger.error(f"Failed to count documents in {collection_name}: {e}")
            return None

    def aggregate(self, collection_name: str, pipeline: List[Dict]) -> Optional[List[Dict]]:
        """Perform an aggregation pipeline on a collection.

        Args:
            collection_name: Name of the collection
            pipeline: Aggregation pipeline

        Returns:
            Aggregation results or None if aggregation failed
        """
        try:
            collection = self.get_collection(collection_name)
            results = list(collection.aggregate(pipeline))
            return json.loads(json.dumps(results, cls=MongoEncoder))
        except PyMongoError as e:
            logger.error(f"Failed to perform aggregation on {collection_name}: {e}")
            return None

    def distinct(self, collection_name: str, field: str, query: Dict = None) -> Optional[List]:
        """Get distinct values for a field.

        Args:
            collection_name: Name of the collection
            field: Field to get distinct values for
            query: Query to filter documents (default: {})

        Returns:
            List of distinct values or None if failed
        """
        query = query or {}
        try:
            collection = self.get_collection(collection_name)
            results = collection.distinct(field, query)
            return json.loads(json.dumps(results, cls=MongoEncoder))
        except PyMongoError as e:
            logger.error(f"Failed to get distinct values in {collection_name}: {e}")
            return None

    def find_one_and_update(
        self, collection_name: str, query: Dict, update: Dict, return_updated: bool = False, upsert: bool = False
    ) -> Optional[Dict]:
        """Find a document and update it in one atomic operation.

        Args:
            collection_name: Name of the collection
            query: Query to find the document
            update: Update operations to apply
            return_updated: Whether to return the updated document (default: False)
            upsert: Whether to insert if document doesn't exist (default: False)

        Returns:
            Document before or after update, or None if failed
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.find_one_and_update(
                query, update, return_document=True if return_updated else False, upsert=upsert
            )

            if result:
                return json.loads(json.dumps(result, cls=MongoEncoder))
            return None
        except PyMongoError as e:
            logger.error(f"Failed to find and update document in {collection_name}: {e}")
            return None

    def find_one_and_delete(self, collection_name: str, query: Dict) -> Optional[Dict]:
        """Find a document and delete it in one atomic operation.

        Args:
            collection_name: Name of the collection
            query: Query to find the document

        Returns:
            Deleted document or None if not found or failed
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.find_one_and_delete(query)

            if result:
                return json.loads(json.dumps(result, cls=MongoEncoder))
            return None
        except PyMongoError as e:
            logger.error(f"Failed to find and delete document in {collection_name}: {e}")
            return None

    def bulk_write(self, collection_name: str, operations: List) -> Optional[Dict]:
        """Perform bulk write operations.

        Args:
            collection_name: Name of the collection
            operations: List of write operations

        Returns:
            Dict with operation counts or None if failed
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.bulk_write(operations)

            response = {
                "inserted_count": result.inserted_count,
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "deleted_count": result.deleted_count,
                "upserted_count": result.upserted_count,
                "upserted_ids": [str(id) for id in result.upserted_ids.values()] if result.upserted_ids else [],  # noqa
            }

            logger.info(f"Performed bulk write in {collection_name}: {response}")
            return response
        except PyMongoError as e:
            logger.error(f"Failed to perform bulk write in {collection_name}: {e}")
            return None
