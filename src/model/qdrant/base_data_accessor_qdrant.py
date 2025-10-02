import base64
import copy
import logging
import re
from datetime import datetime
from typing import Any, Collection

import farmhash
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    DatetimeRange,
    FieldCondition,
    Filter,
    MatchValue,
    Record,
)

from dto.item import ItemDto
from exceptions.empty_search_error import EmptySearchError
from model.base_data_accessor import BaseDataAccessor
from util.dto_utils import update_from_props

logger = logging.getLogger(__name__)


class BaseDataAccessorQdrant(BaseDataAccessor):
    def __init__(
        self, client: QdrantClient, collection_name: str, field_mapping: dict[str, str]
    ):
        self._client = client
        self._collection_name = collection_name
        self._field_mapping = field_mapping
        self._max_items_per_fetch = 500

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

    def get_items_by_ids(
        self, item: ItemDto, ids: Collection[str], provenance="c2c_models"
    ) -> list[ItemDto]:
        fingerprints = [farmhash.fingerprint64(id) for id in ids]
        response = self._client.retrieve(
            collection_name=self._collection_name, ids=fingerprints, with_payload=True
        )
        return self.__get_items_from_response(item, response)

    def _get_item_by_column_value(self, item: ItemDto, column: str, value: Any):
        print("Searching for column: " + column + " with value: " + str(value))
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

    def get_item_by_urn(self, item: ItemDto, urn: str, filter=None) -> list[ItemDto]:
        return self._get_item_by_column_value(item, "urn", urn)

    def get_item_by_crid(self, item: ItemDto, crid, filter=None):
        return self._get_item_by_column_value(
            item=item,
            column=self._field_mapping.get("crid", "crid"),
            value=crid.strip(),
        )

    def get_item_by_url(self, item: ItemDto, url, filter=None):
        last_string = re.search(r".*/([^/?]+)[?]*", url.strip()).group(1)
        base64_bytes = last_string.encode("ascii")
        crid_bytes = base64.b64decode(base64_bytes + b"==")
        crid = crid_bytes.decode("ascii")
        return self.get_item_by_crid(item, crid)

    def get_item_by_cms_id(self, item: ItemDto, cms_id: str, filter=None):
        return self._get_item_by_column_value(item=item, column="cmsId", value=cms_id)

    def get_item_by_text(self, item: ItemDto, text, filter={}):
        item_dtos = []
        new_item = copy.copy(item)
        new_item._is_draft = True
        text_input = {"description": text}
        new_item = update_from_props(new_item, text_input, self._field_mapping)
        item_dtos.append(new_item)
        return item_dtos, 1

    def get_items_by_date(
        self,
        item: ItemDto,
        start_date: datetime,
        end_date: datetime,
        item_filter={},
        offset=10,
        size=-1,
    ) -> list[ItemDto]:
        size = (
            self._max_items_per_fetch
            if size < 0
            else min(size, self._max_items_per_fetch)
        )

        if start_date > end_date:
            logger.info(
                f"end data for data selection. {end_date} is before start date {start_date}. Swapping end and start date."
            )
            start_date, end_date = end_date, start_date

        filters = [
            FieldCondition(key=column, match=MatchValue(value=value))
            for column, value in item_filter.items()
        ]

        response, _ = self._client.scroll(
            collection_name=self._collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="availableFrom",
                        range=DatetimeRange(gte=start_date, lt=end_date),
                    ),
                    *filters,
                ]
            ),
            limit=size,
            with_payload=True,
        )
        return self.__get_items_from_response(item, response)
