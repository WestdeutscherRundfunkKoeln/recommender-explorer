from opensearchpy import OpenSearch, RequestsHttpConnection, helpers, NotFoundError
from typing import Any, Iterator, Self
import logging
import json

from src.models import CreateDocumentRequest

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


class OssAccessor:
    def __init__(self, index: str, client: OpenSearch) -> None:
        self.target_idx_name = index
        self.oss_client = client

    @classmethod
    def from_config(cls, config) -> Self:
        index = config["opensearch"]["index"]

        host = config["opensearch"]["host"]
        user = config["opensearch"]["user"]
        password = config["opensearch"]["pass"]
        port = config["opensearch"]["port"]
        use_ssl = config["deployment_env"] != "LOCAL"

        logger.info("Host: " + host)
        client = OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_auth=(user, password),
            use_ssl=use_ssl,
            verify_certs=use_ssl,
            connection_class=RequestsHttpConnection,
            timeout=600,
        )

        return cls(index, client)

    def create_oss_doc(self, data: CreateDocumentRequest):
        # add document to index
        print(data, type(data))
        response = self.oss_client.update(
            index=self.target_idx_name,
            body={"doc": data.model_dump(), "doc_as_upsert": True},
            id=data.id,
            refresh=True,
        )

        logger.info("Response: " + json.dumps(response, indent=4, default=str))

        return response

    def delete_oss_doc(self, id: str):
        try:
            response = self.oss_client.delete(index=self.target_idx_name, id=id)
        except NotFoundError:
            response = {
                "_index": self.target_idx_name,
                "_id": id,
                "_version": 0,
                "result": "id not found",
                "_shards": {"total": 0, "successful": 0, "failed": 0},
                "_seq_no": 0,
                "_primary_term": 0,
            }
        return response

    def bulk_ingest(self, jsonlst: dict) -> None:
        for success, info in helpers.parallel_bulk(
            client=self.oss_client,
            index=self.target_idx_name,
            actions=self.doc_generator(jsonlst),
        ):
            if not success:
                print("A document failed:", info)

    def doc_generator(
        self, jsonlst: dict
    ) -> Iterator[dict[str, Any]]:  # TODO: review this
        for item in jsonlst.values():
            yield {
                "_op_type": "update",
                "_index": self.target_idx_name,
                "_id": item.id,
                "_source": {"doc": item.model_dump(), "doc_as_upsert": True},
            }
