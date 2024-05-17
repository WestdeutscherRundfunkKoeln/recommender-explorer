import logging
import httpx

from model.nn_seeker import NnSeeker
from opensearchpy import OpenSearch, RequestsHttpConnection
from dto.item import ItemDto

logger = logging.getLogger(__name__)


class NnSeekerOpenSearch(NnSeeker):
    FILTER_TYPE_SAME_GENRE = "same_genre"
    ITEM_IDENTIFIER_PROP = "id"

    def __init__(self, config):
        auth = (config["opensearch.user"], config["opensearch.pass"])

        self.client = OpenSearch(
            hosts=[
                {"host": config["opensearch.host"], "port": config["opensearch.port"]}
            ],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )
        self.target_idx_name = config["opensearch.index"]

        self.__max_num_neighbours = 50
        self.max_items_per_fetch = 500
        self.field_mapping = config["opensearch.field_mapping"]

        self.embedding_field_name = "embedding_01"

        self.base_url_embedding = config.get("ingest.base_url_embedding")
        self.api_key = config.get("ingest.api_key")

    def set_model_config(self, model_config):
        self._set_model_name(model_config["endpoint"].removeprefix("opensearch://"))

    def _set_model_name(self, model_name):
        self.embedding_field_name = model_name

    def get_k_NN(self, item: ItemDto, k, filter_criteria) -> tuple[list, list]:
        logger.info(f"Seeking {k} neighours.")
        content_id = item.id

        if content_id:
            embedding = self.__get_vec_for_content_id(content_id)
        else:
            text_to_embed = item.description
            request_payload = {"embedText": text_to_embed}
            response = httpx.post(
                f"{self.base_url_embedding}/embedding",
                json=request_payload,
                timeout=None,
                headers={"x-api-key": self.api_key},
            ).json()
            embedding = response[self.embedding_field_name]

        recomm_content_ids, nn_dists = self.__get_nn_by_embedding(
            embedding, k, filter_criteria
        )
        return recomm_content_ids, nn_dists, self.ITEM_IDENTIFIER_PROP

    def get_max_num_neighbours(self, content_id):
        return self.__max_num_neighbours

    def set_max_num_neighbours(self, num_neighbours):
        self.__max_num_neighbours = num_neighbours

    def __get_nn_by_embedding(self, embedding, k, filter_criteria):
        return self.__get_exact__nn_by_embedding(embedding, k, filter_criteria)

    def __get_exact__nn_by_embedding(self, embedding, k, filter_criteria):
        query = self.__compose_exact_nn_by_embedding_query(
            embedding, k, filter_criteria
        )
        logger.info(query)
        response = self.client.search(body=query, index=self.target_idx_name)
        hits = response["hits"]["hits"]
        nn_dists = [(hit["_score"] - 1) for hit in hits]
        ids = [hit["_source"]["id"] for hit in hits]
        return ids, nn_dists

    def __compose_exact_nn_by_embedding_query(self, embedding, k, reco_filter):
        query = {
            "size": k,
            "_source": {"include": "id"},
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
                        },
                    },
                }
            },
        }

        sub_query = {}

        # add boolean expressions
        if reco_filter.get("bool"):
            sub_query["bool"] = reco_filter["bool"]
        if not sub_query:
            sub_query["match_all"] = {}

        # assign it to the subquery
        query["query"]["script_score"]["query"] = sub_query

        # add sorting
        if reco_filter.get("sort"):
            query["sort"] = [
                {self.field_mapping["created"]: {"order": reco_filter["sort"]}}
            ]
            query["track_scores"] = True

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
        embedding = response["hits"]["hits"][0]["_source"][self.embedding_field_name]

        return embedding
