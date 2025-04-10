from unittest.mock import MagicMock

import pytest
from bson import ObjectId

from app.infrastructure.mongo.data import MongoDBData
from app.infrastructure.mongo.engine import MongoDBEngine


@pytest.fixture
def mock_engine():
    """Fixture to provide a mocked MongoDBEngine."""
    return MagicMock(spec=MongoDBEngine)


@pytest.fixture
def mongo_data(mock_engine):
    """Fixture to provide a MongoDBData instance with a mocked engine."""
    return MongoDBData(engine=mock_engine)


def test_init(mongo_data, mock_engine):
    """Test the initialization of MongoDBData."""
    assert mongo_data.engine == mock_engine, "Engine should be correctly assigned"


def test_insert_one(mongo_data, mock_engine):
    """Test the insert_one method."""
    mock_collection = MagicMock()
    mock_engine.get_collection.return_value = mock_collection
    mock_collection.insert_one.return_value.inserted_id = ObjectId("64b64c7f8f8b9a1d4c8e4e9a")

    document = {"name": "test"}
    result = mongo_data.insert_one("test_collection", document)

    mock_engine.get_collection.assert_called_once_with("test_collection")
    mock_collection.insert_one.assert_called_once_with(document)
    assert result == "64b64c7f8f8b9a1d4c8e4e9a", "Inserted ID should match"


def test_find_one(mongo_data, mock_engine):
    """Test the find_one method."""
    mock_collection = MagicMock()
    mock_engine.get_collection.return_value = mock_collection
    mock_collection.find_one.return_value = {"_id": ObjectId("64b64c7f8f8b9a1d4c8e4e9a"), "name": "test"}

    query = {"name": "test"}
    result = mongo_data.find_one("test_collection", query)

    mock_engine.get_collection.assert_called_once_with("test_collection")
    mock_collection.find_one.assert_called_once_with(query)
    assert result["_id"] == "64b64c7f8f8b9a1d4c8e4e9a", "Returned document ID should match"
    assert result["name"] == "test", "Returned document name should match"


def test_update_one(mongo_data, mock_engine):
    """Test the update_one method."""
    mock_collection = MagicMock()
    mock_engine.get_collection.return_value = mock_collection
    mock_collection.update_one.return_value.matched_count = 1
    mock_collection.update_one.return_value.modified_count = 1
    mock_collection.update_one.return_value.upserted_id = None

    query = {"name": "test"}
    update = {"$set": {"name": "updated"}}
    result = mongo_data.update_one("test_collection", query, update)

    mock_engine.get_collection.assert_called_once_with("test_collection")
    mock_collection.update_one.assert_called_once_with(query, update, upsert=False)
    assert result["matched_count"] == 1, "Matched count should be 1"
    assert result["modified_count"] == 1, "Modified count should be 1"
    assert result["upserted_id"] is None, "Upserted ID should be None"


def test_delete_one(mongo_data, mock_engine):
    """Test the delete_one method."""
    mock_collection = MagicMock()
    mock_engine.get_collection.return_value = mock_collection
    mock_collection.delete_one.return_value.deleted_count = 1

    query = {"name": "test"}
    result = mongo_data.delete_one("test_collection", query)

    mock_engine.get_collection.assert_called_once_with("test_collection")
    mock_collection.delete_one.assert_called_once_with(query)
    assert result == 1, "Deleted count should be 1"
