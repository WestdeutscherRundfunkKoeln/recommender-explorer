import copy
import logging
import collections
import pandas as pd
import re
import base64
import constants

from dataclasses import dataclass, fields
from opensearchpy import OpenSearch, RequestsHttpConnection
from datetime import datetime
from model.base_data_accessor import BaseDataAccessor
from exceptions.empty_search_error import EmptySearchError
from dto.item import ItemDto
from util.dto_utils import content_fields, update_from_props, get_primary_idents

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
                + item_ident,
                {},
            )
        else:
            return response["hits"]["hits"][0]["_id"]

    def get_items_by_ids(
        self, item: ItemDto, ids, provenance=constants.ITEM_PROVENANCE_C2C
    ):
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

        # logger.info(response)
        return self.__get_items_from_response(item, response, provenance)

    def get_item_by_url(self, item: ItemDto, url, filter={}):
        last_string = re.search(r".*/([^/?]+)[?]*", url.strip()).group(1)
        base64_bytes = last_string.encode("ascii")
        crid_bytes = base64.b64decode(base64_bytes + b"==")
        crid = crid_bytes.decode("ascii")
        return self.get_item_by_crid(item, crid, filter)

    def get_item_by_urn(self, item: ItemDto, urn, filter={}):
        urn = urn.strip()
        prim_id, prim_val = get_primary_idents(self.config)
        oss_col = prim_val + ".keyword"
        query = {
            "size": 10,  # duplicate crids max occur in data, return max 10
            "_source": {"exclude": "embedding"},
            "query": {
                "match": {oss_col: urn},
            },
        }

        logger.info(query)
        response = self.client.search(body=query, index=self.target_idx_name)
        return self.__get_items_from_response(item, response)

    def get_item_by_crid(self, item: ItemDto, crid, filter={}):
        """Builds query to get items based on a crid

        Maps crid parameter to mapped value if given in configuration file.
        Creates and executes the query for opensearch service.

        :param item: Item Dto from given component
        :param crid: Value of crid from component
        :param filter:
        :return: Response from opensearch service for crid query
        """
        crid = crid.strip()
        column = "crid"
        # apply field mapping if defined
        if column in self.field_mapping.keys():
            new_col = self.field_mapping[column]
            logger.info(f"mapping col {column} to {new_col}")
            column = new_col

        # term filter applies to keyword subcolumn
        oss_col = column + ".keyword"

        query = {
            "size": 10,  # duplicate crids max occur in data, return max 10
            "_source": {"exclude": "embedding"},
            "query": {
                "match": {oss_col: crid},
            },
        }

        logger.info(query)
        response = self.client.search(body=query, index=self.target_idx_name)
        return self.__get_items_from_response(item, response)

    def get_item_by_text(self, item: ItemDto, text, filter={}):
        item_dtos = []
        new_item = copy.copy(item)
        text_input = {"description": text}
        new_item = update_from_props(new_item, text_input, self.field_mapping)
        item_dtos.append(new_item)
        return item_dtos, 1

    def get_items_by_date(
        self, item: ItemDto, start_date, end_date, item_filter={}, offset=10, size=-1
    ) -> tuple[pd.DataFrame, int]:
        # handle valid size range

        if size < 0 or size > self.max_items_per_fetch:
            size = self.max_items_per_fetch

        if start_date > end_date:
            logger.info(
                f"end data for data selection. {end_date} is before start date {start_date}. Swapping end and start date."
            )
            xx = end_date
            end_date = start_date
            start_date = xx

        start_date_d = pd.to_datetime(start_date).strftime("%Y-%m-%d")
        end_date_d = pd.to_datetime(end_date).strftime("%Y-%m-%d")
        query = self.__compose_date_range_query(
            size, offset, [start_date_d, end_date_d], item_filter
        )
        logger.info(f"query: {query}")
        response = self.client.search(body=query, index=self.target_idx_name)
        return self.__get_items_from_response(item, response)

    def get_items_date_range_limits(self) -> tuple[pd.Timestamp, pd.Timestamp]:
        query = {
            "size": 0,
            "query": {"match_all": {}},
            "aggs": {
                "min_date": {"min": {"field": self.field_mapping["created"]}},
                "max_date": {"max": {"field": self.field_mapping["created"]}},
            },
        }

        response = self.client.search(body=query, index=self.target_idx_name)
        min_date = response["aggregations"]["min_date"]["value_as_string"]
        max_date = response["aggregations"]["max_date"]["value_as_string"]
        newest_item_in_base_ts = pd.Timestamp(max_date).timestamp()
        oldest_item_in_base_ts = pd.Timestamp(min_date).timestamp()
        return newest_item_in_base_ts, oldest_item_in_base_ts

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

    def __get_items_from_response(
        self, item: ItemDto, response, provenance=constants.ITEM_PROVENANCE_C2C
    ) -> tuple[list, int]:
        """Gets the resulting items from the opensearch services response

        Gets total items count from search response (hits.total.hits) and iterates
        over result items (hits.hits._source)

        :param item: Item dto from the given component
        :param response: Response from opensearch service for created query
        :param provenance:
        :return: List of item dtos, total items count
        """
        total_items = response["hits"]["total"]["value"]

        items = [x["_source"] for x in response["hits"]["hits"]]
        if total_items < 1 or not len(items):
            raise EmptySearchError("Keine Treffer gefunden", {})
        item_dtos = []
        for opensearch_hit in items:
            new_item = copy.copy(item)
            new_item = update_from_props(new_item, opensearch_hit, self.field_mapping)
            item_dtos.append(new_item)
        return item_dtos, total_items

    def __compose_date_range_query(self, size, offset, dates, item_filter) -> dict:
        query = {
            "size": size,
            "from": offset,
            "_source": {"exclude": "embedding*"},
            "query": {
                "bool": {
                    "must": [
                        {"range": {"availableFrom": {"gte": dates[0], "lt": dates[1]}}},
                    ]
                }
            },
            "sort": [{self.field_mapping["created"]: {"order": "asc"}}],
        }

        for filter_category in item_filter.items():
            term = collections.defaultdict(dict)
            if len(filter_category[1]) > 0:
                term["terms"][filter_category[0] + ".keyword"] = filter_category[1]
                query["query"]["bool"]["must"].append(term)
        return query
