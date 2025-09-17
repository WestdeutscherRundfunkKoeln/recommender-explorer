import copy
from typing import Collection

import farmhash
from qdrant_client import QdrantClient

from src.dto.item import ItemDto
from src.model.base_data_accessor import BaseDataAccessor
from src.util.dto_utils import update_from_props


class BaseDataAccessorQdrant(BaseDataAccessor):
    def __init__(
        self, client: QdrantClient, collection_name: str, field_mapping: dict[str, str]
    ):
        self._client = client
        self._collection_name = collection_name
        self._field_mapping = field_mapping

    @classmethod
    def from_config(cls, config) -> "BaseDataAccessorQdrant":
        return cls(
            client=QdrantClient(
                url=config["qdrant.url"],
                api_key=config["qdrant.api_key"],
            ),
            collection_name=config["qdrant.collection_name"],
            field_mapping=config["qdrant.field_mapping"],
        )

    def get_items_by_ids(self, item: ItemDto, ids: Collection[str]) -> list[ItemDto]:
        fingerprints = [farmhash.fingerprint64(id) for id in ids]
        records = self._client.retrieve(
            collection_name=self._collection_name, ids=fingerprints, with_payload=True
        )
        return [
            update_from_props(
                copy.copy(item),
                record.payload if record.payload else {},
                self._field_mapping,
            )
            for record in records
        ]

    def get_primary_key_by_field(self, item_ident, field):
        pass

    def get_unique_vals_for_column(self, column, sort=True):
        pass
