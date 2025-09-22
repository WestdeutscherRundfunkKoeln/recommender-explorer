import pytest
from dataclasses import dataclass
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from src.dto.item import ItemDto
from src.model.qdrant.base_data_accessor_qdrant import BaseDataAccessorQdrant
from test.unit.model.qdrant.conftest import COLLECTION_NAME


@dataclass
class TestData(ItemDto):
    field1: str = ""
    field3: str = ""

    @property
    def viewer(self) -> str:
        return ""


def test_get_items_by_ids(qdrant_client: QdrantClient):
    accessor = BaseDataAccessorQdrant(
        qdrant_client, collection_name=COLLECTION_NAME, field_mapping={}
    )

    items = accessor.get_items_by_ids(
        TestData("test", "test", "test"), ["test1", "test2"]
    )
    assert items == [
        TestData("test", "test", "test", field1="test1"),
        TestData("test", "test", "test", field1="test1"),
    ]


def test_get_items_by_ids_not_found(qdrant_client: QdrantClient):
    accessor = BaseDataAccessorQdrant(
        qdrant_client, collection_name=COLLECTION_NAME, field_mapping={}
    )
    items = accessor.get_items_by_ids(TestData("test", "test", "test"), ["test"])
    assert items == []


def test_get_items_by_ids_invalid_collection(qdrant_client: QdrantClient):
    accessor = BaseDataAccessorQdrant(
        qdrant_client, collection_name="invalid", field_mapping={}
    )
    with pytest.raises(UnexpectedResponse):
        accessor.get_items_by_ids(TestData("test", "test", "test"), ["test"])


def test_get_items_by_ids_with_field_mapping(qdrant_client: QdrantClient):
    accessor = BaseDataAccessorQdrant(
        qdrant_client,
        collection_name=COLLECTION_NAME,
        field_mapping={"field3": "field2"},
    )

    items = accessor.get_items_by_ids(
        TestData("test", "test", "test"), ["test1", "test2"]
    )
    assert items == [
        TestData("test", "test", "test", field1="test1", field3="test2"),
        TestData("test", "test", "test", field1="test1", field3="test2"),
    ]
