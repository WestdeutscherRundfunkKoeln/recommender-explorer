import pytest
from dataclasses import dataclass
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from src.dto.item import ItemDto
from exceptions.empty_search_error import EmptySearchError
from src.model.qdrant.base_data_accessor_qdrant import BaseDataAccessorQdrant
from test.unit.model.qdrant.conftest import COLLECTION_NAME


@dataclass
class TestData(ItemDto):
    field1: str = ""
    field0: str = ""

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
        field_mapping={"field0": "field2"},
    )

    items = accessor.get_items_by_ids(
        TestData("test", "test", "test"), ["test1", "test2"]
    )
    assert items == [
        TestData("test", "test", "test", field1="test1", field0="test2"),
        TestData("test", "test", "test", field1="test1", field0="test2"),
    ]


def test_get_primary_key_by_field(qdrant_client: QdrantClient):
    accessor = BaseDataAccessorQdrant(
        qdrant_client, collection_name=COLLECTION_NAME, field_mapping={}
    )
    pk = accessor.get_primary_key_by_field("test1", "field3")
    assert pk == "test1"

    pk = accessor.get_primary_key_by_field("test2", "field3")
    assert pk == "test2"


def test_get_primary_key_by_field_not_found(qdrant_client: QdrantClient):
    accessor = BaseDataAccessorQdrant(
        qdrant_client, collection_name=COLLECTION_NAME, field_mapping={}
    )
    with pytest.raises(EmptySearchError):
        accessor.get_primary_key_by_field("test", "field3")


def test_get_unique_vals_for_column(qdrant_client: QdrantClient):
    accessor = BaseDataAccessorQdrant(
        qdrant_client, collection_name=COLLECTION_NAME, field_mapping={}
    )
    vals = accessor.get_unique_vals_for_column("field3")
    assert set(vals) == {"test1", "test2", "test3"}

    vals = accessor.get_unique_vals_for_column("field1")
    assert set(vals) == {"test1"}


def test_get_unique_vals_for_column_unknown_field(qdrant_client: QdrantClient):
    accessor = BaseDataAccessorQdrant(
        qdrant_client, collection_name=COLLECTION_NAME, field_mapping={}
    )
    vals = accessor.get_unique_vals_for_column("unknown")
    assert set(vals) == set()
