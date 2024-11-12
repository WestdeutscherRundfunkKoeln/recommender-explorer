import json
import logging
from typing import Any, Iterator

import sys

if (
    sys.version_info.major == 3 and sys.version_info.minor < 11
):  # if python version is lower than 3.11
    from typing_extensions import Self
else:
    from typing import Self

from fastapi import HTTPException
from opensearchpy import (
    OpenSearch,
    RequestError,
    RequestsHttpConnection,
    helpers,
)

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

    def create_oss_doc(self, id: str, data: dict[str, Any]):
        # add document to index
        response = self.oss_client.update(
            index=self.target_idx_name,
            body={"doc": data, "doc_as_upsert": True},
            id=id,
            refresh=True,
        )

        logger.info(
            "Response os OSS update: " + json.dumps(response, indent=4, default=str)
        )

        return response

    def delete_oss_doc(self, id: str):
        return self.oss_client.delete(index=self.target_idx_name, id=id)

    def bulk_ingest(self, jsonlst: dict[str, dict]) -> None:
        for success, info in helpers.parallel_bulk(
            client=self.oss_client,
            index=self.target_idx_name,
            raise_on_error=False,
            raise_on_exception=False,
            actions=self.doc_generator(jsonlst),
        ):
            if not success:
                print("A document failed:", info)

    def doc_generator(
        self, jsonlst: dict[str, dict]
    ) -> Iterator[dict[str, Any]]:  # TODO: review this
        for id, item in jsonlst.items():
            yield {
                "_op_type": "update",
                "_index": self.target_idx_name,
                "_id": id,
                "_source": {"doc": item, "doc_as_upsert": True},
            }

    def get_oss_doc(self, id: str, fields: list[str]) -> dict:
        return self.oss_client.get(
            index=self.target_idx_name,
            id=id,
            params={"_source_includes": ",".join(fields)},
        )

    def get_oss_docs(self, query: dict[str, str]) -> dict:
        try:
            return self.oss_client.search(index=self.target_idx_name, body=query)
        except RequestError as e:
            raise HTTPException(
                detail=f"Invalid query: {e.info}", status_code=400
            ) from e

    def scan_oss_docs(self, query: dict[str, str]) -> list[dict]:
        try:
            return list(
                helpers.scan(self.oss_client, query=query, index=self.target_idx_name)
            )
        except RequestError as e:
            raise HTTPException(
                detail=f"Invalid query: {e.info}", status_code=400
            ) from e
