import copy
from typing import Any, Collection

import farmhash
from qdrant_client import QdrantClient
from qdrant_client.http.models import FieldCondition, Filter, MatchValue, Record

from dto.item import ItemDto
from model.base_data_accessor import BaseDataAccessor
from util.dto_utils import update_from_props
from exceptions.empty_search_error import EmptySearchError


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
        response = self._client.retrieve(
            collection_name=self._collection_name, ids=fingerprints, with_payload=True
        )
        return self.__get_items_from_response(item, response)

    def _get_item_by_column_value(self, item: ItemDto, column: str, value: Any):
        response, _ = self._scroll_points_by_column_value(column, value)
        return self.__get_items_from_response(item, response)

    def _scroll_points_by_column_value(self, column: str, value: Any, limit=1):
        return self._client.scroll(
            collection_name=self._collection_name,
            scroll_filter=Filter(
                must=FieldCondition(key=column, match=MatchValue(value=value))
            ),
            limit=limit,
            with_payload=True,
        )

    def __get_items_from_response(
        self, item: ItemDto, records: Collection[Record]
    ) -> list[ItemDto]:
        return [
            update_from_props(
                copy.copy(item),
                record.payload if record.payload else {},
                self._field_mapping,
            )
            for record in records
        ]

    def get_primary_key_by_field(self, item_ident: str, field: str):
        response, _ = self._scroll_points_by_column_value(field, item_ident)
        if not response:
            raise EmptySearchError(
                f"Couldn't find item identified by field [{field}] and value [{item_ident}]",
                {},
            )
        return response[0].payload["content_id"]

    def get_unique_vals_for_column(self, column, sort=True, limit=1000):
        vals = set()
        offset = 0

        while len(vals) < limit:
            response, _ = self._client.scroll(
                collection_name=self._collection_name,
                offset=offset,
                limit=limit,
                with_payload=[column],
            )

            if not response:
                break

            for record in response:
                if len(vals) >= limit:
                    break
                if record and record.payload and column in record.payload:
                    vals.add(record.payload[column])

            offset = max(int(record.id) for record in response) + 1

        result = list(vals)
        return sorted(result) if sort else result

    def get_item_by_urn(self, item: ItemDto, urn: str) -> list[ItemDto]:
        return self._get_item_by_column_value(item, "urn", urn)
