import copy
import logging
from typing import Collection

from opensearchpy import OpenSearch, RequestsHttpConnection
from model.base_data_accessor import BaseDataAccessor
from exceptions.empty_search_error import EmptySearchError
from dto.item import ItemDto
from util.dto_utils import update_from_props, get_primary_idents

# loggin preference
logger = logging.getLogger(__name__)


class BaseDataAccessorOpenSearch(BaseDataAccessor):
    def __init__(self, config):
        self.config = config

        auth = (self.config["opensearch.user"], self.config["opensearch.pass"])

        use_ssl = self.config.get("opensearch.use_ssl", True)

        self.client = OpenSearch(
            hosts=[
                {
                    "host": config["opensearch.host"],
                    "port": self.config["opensearch.port"],
                }
            ],
            http_auth=auth,
            use_ssl=use_ssl,
            verify_certs=use_ssl,
            connection_class=RequestsHttpConnection,
        )
        self.target_idx_name = self.config["opensearch.index"]
        self.field_mapping = self.config["opensearch.field_mapping"]
        self.embedding_field_name = "embedding"

        self.max_items_per_fetch = 500

    def get_primary_key_by_field(self, item_ident, field):
        query = {
            "query": {"match": {field + ".keyword": item_ident}},
            "size": 1,
            "_source": {"exclude": "embedding"},
        }
        logger.info(query)
        response = self.client.search(body=query, index=self.target_idx_name)

        if response["hits"]["total"]["value"] < 1:
            raise EmptySearchError(
                "Couldn't find item identified by field ["
                + field
                + ".keyword] and value ["
                + item_ident
                + "]",
                {},
            )
        else:
            return response["hits"]["hits"][0]["_id"]

    def get_items_by_ids(self, item: ItemDto, ids: Collection[str]) -> list[ItemDto]:
        if len(ids) <= 0:
            return []

        docs = [
            {
                "_id": id,
                "_source": {
                    "exclude": "embedding"
                },  # Todo: replace by all model fields
            }
            for id in ids
        ]

        query = {"docs": docs}

        logger.info(query)
        response_mget = self.client.mget(body=query, index=self.target_idx_name)
        response = {
            "hits": {"hits": response_mget["docs"], "total": {"value": len(ids)}}
        }
        return self.__get_items_from_response(item, response)

    def _get_item_by_column_value(self, item: ItemDto, column: str, value: str):
        oss_col = column + ".keyword"
        query = {
            "size": 10,  # duplicate crids max occur in data, return max 10
            "_source": {"exclude": "embedding"},
            "query": {
                "match": {oss_col: value},
            },
        }
        logger.info(query)
        response = self.client.search(body=query, index=self.target_idx_name)
        return self.__get_items_from_response(item, response)

    def get_item_by_urn(self, item: ItemDto, urn: str):
        urn = urn.strip()
        _, prim_val = get_primary_idents(self.config)
        return self._get_item_by_column_value(item=item, column=prim_val, value=urn)

    def get_top_k_vals_for_column(self, column, k) -> list:
        # apply field mapping if defined
        if column in self.field_mapping.keys():
            new_col = self.field_mapping[column]
            logger.info(f"mapping col {column} to {new_col}")
            column = new_col

        # term filter applies to keyword subcolumn
        oss_col = column + ".keyword"

        query = {
            "size": 0,
            "_source": {"exclude": "*"},
            "query": {"match_all": {}},
            "aggs": {"mydata_agg": {"terms": {"field": oss_col, "size": k}}},
        }
        logger.info(query)
        response = self.client.search(body=query, index=self.target_idx_name)
        buckets = response["aggregations"]["mydata_agg"]["buckets"]
        vals = [bucket["key"] for bucket in buckets]
        top_col_vals = vals
        return top_col_vals

    def get_unique_vals_for_column(self, column, sort=True, max_vals=1000) -> list:
        uniq_vals = self.get_top_k_vals_for_column(column, k=max_vals)
        if sort:
            uniq_vals = sorted(uniq_vals)
        return uniq_vals

    def __get_items_from_response(self, item: ItemDto, response) -> list[ItemDto]:
        """Gets the resulting items from the opensearch services response

        Gets total items count from search response (hits.total.hits) and iterates
        over result items (hits.hits._source)

        :param item: Item dto from the given component
        :param response: Response from opensearch service for created query
        :param provenance:
        :return: List of item dtos, total items count
        """
        total_items = response["hits"]["total"]["value"]
        items = []
        for x in response["hits"]["hits"]:
            if "_source" in x:
                items.append(x["_source"])

        if total_items < 1 or not len(items):
            raise EmptySearchError("Keine Treffer gefunden", {})
        item_dtos = []
        for opensearch_hit in items:
            new_item = copy.copy(item)
            new_item = update_from_props(new_item, opensearch_hit, self.field_mapping)
            item_dtos.append(new_item)
        return item_dtos
