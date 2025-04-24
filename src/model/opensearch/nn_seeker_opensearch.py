import collections
import logging
from typing import Any

import httpx
from dto.item import ItemDto
from envyaml import EnvYAML
from model.nn_seeker import NnSeeker
from opensearchpy import OpenSearch, RequestsHttpConnection
from exceptions.embedding_not_found_error import UnknownItemEmbeddingError

logger = logging.getLogger(__name__)


class NnSeekerOpenSearch(NnSeeker):
    FILTER_TYPE_SAME_GENRE = "same_genre"
    ITEM_IDENTIFIER_PROP = "id"
    FILTER_LOGIC_MATRIX = {
        "same": "must",
        "different": "must_not",
        "choose": "must",
        "mixed": "",
    }
    FILTER_FIELD_MATRIX = {
        "genre": "genreCategory",
        "subgenre": "subgenreCategories",
        "theme": "thematicCategories",
        "show": "showId",
    }

    def __init__(
        self,
        client: OpenSearch,
        target_idx_name: str,
        field_mapping: dict[str, str],
        base_url_embedding: str,
        api_key: str,
        max_num_neighbours: int = 50,
        max_items_per_fetch: int = 500,
        embedding_field_name: str = "embedding_01",
        config_MDP2: str = "./config/mdp2_lookup.yaml",
    ):
        self.client = client
        self.target_idx_name = target_idx_name

        self.__max_num_neighbours = max_num_neighbours
        self.max_items_per_fetch = max_items_per_fetch
        self.field_mapping = field_mapping

        self.embedding_field_name = embedding_field_name

        self.base_url_embedding = base_url_embedding
        self.api_key = api_key
        self.config_MDP2 = EnvYAML(config_MDP2)

    @classmethod
    def from_config(cls, config):
        use_ssl = config.get("opensearch.use_ssl", True)
        return cls(
            client=OpenSearch(
                hosts=[
                    {
                        "host": config["opensearch.host"],
                        "port": config["opensearch.port"],
                    }
                ],
                http_auth=(config["opensearch.user"], config["opensearch.pass"]),
                use_ssl=use_ssl,
                verify_certs=use_ssl,
                connection_class=RequestsHttpConnection,
            ),
            target_idx_name=config["opensearch.index"],
            field_mapping=config["opensearch.field_mapping"],
            base_url_embedding=config["ingest.base_url_embedding"],
            api_key=config["ingest.api_key"],
        )

    def set_model_config(self, model_config):
        self._set_model_name(model_config["endpoint"].removeprefix("opensearch://"))

    def _set_model_name(self, model_name):
        self.embedding_field_name = model_name

    def get_k_NN(
        self, item: ItemDto, k: int, nn_filter: dict[str, Any]
    ) -> tuple[list[str], list[float]]:
        logger.info(f"Seeking {k} neighours.")
        content_id = item.id

        if content_id:
            embedding = self.__get_vec_for_content_id(content_id)
        else:
            embedding = self.__get_vec_for_text_from_endpoint(item)

        reco_filter = self._transpose_reco_filter_state(nn_filter, item)
        recomm_content_ids, nn_dists = self.__get_nn_by_embedding(
            embedding, k, reco_filter
        )

        return recomm_content_ids, nn_dists, "id"

    def get_max_num_neighbours(self, content_id):
        return self.__max_num_neighbours

    def set_max_num_neighbours(self, num_neighbours):
        self.__max_num_neighbours = num_neighbours

    def __get_nn_by_embedding(
        self, embedding: list[float], k: int, filter_criteria: dict[str, Any]
    ) -> tuple[list[str], list[float]]:
        return self.__get_exact__nn_by_embedding(embedding, k, filter_criteria)

    def __get_exact__nn_by_embedding(
        self, embedding: list[float], k: int, filter_criteria: dict[str, Any]
    ) -> tuple[list[str], list[float]]:
        query = self.__compose_exact_nn_by_embedding_query(
            embedding, k, filter_criteria
        )
        logger.info(query)
        response = self.client.search(body=query, index=self.target_idx_name)
        hits = response["hits"]["hits"]
        nn_dists: list[float] = [(hit["_score"] - 1) for hit in hits]
        ids: list[str] = [hit["_id"] for hit in hits]
        return ids, nn_dists

    def __compose_exact_nn_by_embedding_query(
        self, embedding: list[float], k: int, filter_criteria: dict[str, Any]
    ) -> dict[str, Any]:
        query = {
            "size": k,
            "_source": False,
            "query": {
                "script_score": {
                    "query": {},
                    "script": {
                        "source": "knn_score",
                        "lang": "knn",
                        "params": {
                            "field": self.embedding_field_name,
                            "query_value": embedding,
                            "space_type": "cosinesimil",
                            "ignore_unmapped": True,
                        },
                    },
                }
            },
        }

        sub_query = {}

        # add boolean expressions
        if filter_criteria.get("bool"):
            sub_query["bool"] = filter_criteria["bool"]
        if not sub_query:
            sub_query["match_all"] = {}

        # assign it to the subquery
        query["query"]["script_score"]["query"] = sub_query

        # add sorting
        if filter_criteria.get("sort"):
            query["sort"] = [
                {self.field_mapping["created"]: {"order": filter_criteria["sort"]}}
            ]
            query["track_scores"] = True

        if filter_criteria.get("score"):
            query["min_score"] = filter_criteria["score"] + 1

        return query

    def __get_approx_nn_by_embedding(self, embedding, k, filter_criteria):
        query = {
            "size": k,
            "_source": {"include": "id"},
            "query": {
                "knn": {self.embedding_field_name: {"vector": embedding, "k": k}}
            },
        }

        if len(filter_criteria["sortrecos"]):
            query["sort"] = [
                {
                    self.field_mapping["created"]: {
                        "order": filter_criteria["sortrecos"][0]
                    }
                }
            ]
            query["track_scores"] = True

        logger.info(query)
        response = self.client.search(body=query, index=self.target_idx_name)

        hits = response["hits"]["hits"]

        nn_dists = [(1.0 / hit["_score"]) - 1 for hit in hits]
        ids = [hit["_source"]["id"] for hit in hits]

        return ids, nn_dists

    def __get_vec_for_content_id(self, content_id):
        query = {
            "size": 1,
            "_source": {"include": self.embedding_field_name},
            "query": {"bool": {"must": [{"terms": {"id.keyword": [content_id]}}]}},
        }

        logger.info(query)
        response = self.client.search(body=query, index=self.target_idx_name)
        first_hit_source = response.get("hits", {}).get("hits", [{}])[0].get("_source", {})
        if self.embedding_field_name not in first_hit_source:
            raise UnknownItemEmbeddingError(
                'Item with primary id [' + content_id + '] does not have embedding for [' + self.embedding_field_name + ']', {}
            )

        return first_hit_source.get(self.embedding_field_name)

    def __get_vec_for_text_from_endpoint(self, item):
        text_to_embed = item.description
        request_payload = {"embedText": text_to_embed}
        response = httpx.post(
            f"{self.base_url_embedding}/embedding",
            json=request_payload,
            timeout=None,
            headers={"x-api-key": self.api_key},
        ).json()

        if self.embedding_field_name not in response:
            raise UnknownItemEmbeddingError(
                'Text [' + text_to_embed + '] does not have embedding for [' + self.embedding_field_name + ']', {}
            )

        return response[self.embedding_field_name]

    def _transpose_reco_filter_state(
        self, reco_filter: dict[str, Any], start_item: ItemDto
    ) -> dict[str, Any]:
        transposed = collections.defaultdict(dict)
        bool_terms = collections.defaultdict(list)
        script_term = collections.defaultdict(dict)

        self.LIST_FILTER_TERMS = {
            "structurePath": self._prepare_query_term_list_condition_statement,
            "type": self._prepare_query_term_list_condition_statement,
            "keywords": self._prepare_query_term_list_condition_statement,
        }

        for label, value in reco_filter.items():
            if not value:
                continue

            values_list = value

            if isinstance(value, list):
                value = value[0]
            print("🪽🪽🪽🪽🪽🪽🪽🪽🪽")
            print(label)
            print("🪽🪽🪽🪽🪽🪽🪽🪽🪽")
            action, actor = label.split("_")


            match action:
                case "termfilter":
                    bool_terms = self._prepare_query_term_condition_statement(
                        value, start_item, reco_filter, bool_terms
                    )
                case "rangefilter":
                    self._prepare_query_range_condition_statement(value, bool_terms)
                case "relativerangefilter":
                    self._prepare_query_relative_range_condition_statement(
                        start_item, actor, value, bool_terms
                    )
                case "sort":
                    transposed["sort"] = value
                case "score":
                    transposed["score"] = value
                case "clean":
                    script_term = self._prepare_query_bool_script_statement(value)
                case "blacklist":
                    bool_terms["must_not"].append(
                        {
                            "terms": {
                                f"{actor}.keyword": value.replace(" ", "").split(",")
                            }
                        }
                    )
                case captured_action if captured_action in self.LIST_FILTER_TERMS:
                    self.LIST_FILTER_TERMS[captured_action](
                        values_list, captured_action, bool_terms
                    )

                case _:
                    logger.warning(
                        "Received unknown filter action [" + action + "]. Omitting."
                    )

        if bool_terms:
            transposed["bool"] = dict(bool_terms)
        if script_term:
            transposed["bool"]["filter"] = script_term

        return dict(transposed)

    def _prepare_query_range_condition_statement(self, value, bool_terms):
        bool_terms["must"].append({"range": value})

    def _prepare_query_relative_range_condition_statement(
        self, start_item: ItemDto, actor: str, value: float, bool_terms: dict[str, Any]
    ) -> None:
        if hasattr(start_item, actor):
            bool_terms["must"].append(
                {"range": {actor: {"lte": value * start_item.duration}}}
            )
        else:
            logger.warning(
                "Relative range filter could not be applied. Start item has no duration attribute."
            )

    def _prepare_query_term_condition_statement(
        self, value: str, start_item: ItemDto, reco_filter: dict, bool_terms: dict
    ) -> dict:
        transposed_values = []

        logic, field = value.split("_")
        operator = self.FILTER_LOGIC_MATRIX[logic]  ## contains "must"
        if logic != "choose":
            if isinstance(
                start_item.__getattribute__(self.FILTER_FIELD_MATRIX[field]), list
            ):
                transposed_values.extend(
                    start_item.__getattribute__(self.FILTER_FIELD_MATRIX[field])
                )
            else:
                transposed_values.append(
                    start_item.__getattribute__(self.FILTER_FIELD_MATRIX[field])
                )
        else:  ## we're in "choose_genre", or "choose_subgenre" etc..
            if field == "erzählweise":
                reco_filter["value_genreCategory"] = (
                    self.get_genres_and_subgenres_from_upper_category(
                        reco_filter["value_erzaehlweiseCategory"], "genres"
                    )
                )
                field = "genre"
            elif field == "inhalt":
                reco_filter["value_subgenreCategories"] = (
                    self.get_genres_and_subgenres_from_upper_category(
                        reco_filter["value_inhaltCategory"], "subgenres"
                    )
                )
                field = "subgenre"
            filter_key = "value_" + self.FILTER_FIELD_MATRIX[field]
            transposed_values.extend(reco_filter[filter_key])
        term = collections.defaultdict(dict)

        if len(transposed_values):
            term["terms"][self.FILTER_FIELD_MATRIX[field] + ".keyword"] = (
                transposed_values
            )

        if term:
            bool_terms[operator].append(dict(term))

        return bool_terms

    def _prepare_query_bool_script_statement(self, value):
        return {"script": {"script": {"source": f"doc['{value}.keyword'].length > 0"}}}

    def _prepare_query_term_list_condition_statement(
        self, values_list, term, bool_terms
    ):
        bool_terms["must"].append({"terms": {term + ".keyword": values_list}})

    # TODO: this should probably happen somewhere in the controller
    def get_genres_and_subgenres_from_upper_category(
        self, selected_upper_categories, category
    ):  # category = 'genres' or 'subgenres'
        all_selected = []
        for items in selected_upper_categories:
            all_selected.extend(self.config_MDP2["categories_MDP2"][items][category])
        return all_selected
