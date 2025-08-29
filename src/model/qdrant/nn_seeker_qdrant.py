from typing import Any

import farmhash
from qdrant_client import QdrantClient

from dto.item import ItemDto
from src.model.nn_seeker import NnSeeker


class QdrantNNSeeker(NnSeeker):
    def __init__(self, client: QdrantClient):
        self._client = client
        self._collection_name = None

    @classmethod
    def from_config(cls, config) -> "QdrantNNSeeker":
        return cls(
            client=QdrantClient(
                url=config["qdrant.url"],
                api_key=config["qdrant.api_key"],
            ),
        )

    def get_k_NN(
        self, item: ItemDto, k: int, nn_filter: dict[str, Any]
    ) -> tuple[list[str], list, str]:
        assert self._collection_name is not None, (
            "Collection name must be set before querying"
        )
        qdrant_id = farmhash.fingerprint64(item.id)
        search_result = self._client.query_points(
            collection_name=self._collection_name,
            query=qdrant_id,
            limit=k,
            filter=self._build_filter(nn_filter),
        )
        return (
            [str(item.id) for item in search_result.points],
            [item.score for item in search_result.points],
            "",
        )

    def _build_filter(self, nn_filter: dict[str, Any]) -> dict[str, Any]:
        filter = {"must": []}
        for key, value in nn_filter.items():
            match value:
                case list():
                    filter["must"].append({"key": key, "match": {"any": value}})
                case _:
                    filter["must"].append({"key": key, "match": {"value": value}})

        return filter

    def set_model_config(self, model_config) -> None:
        self._collection_name = model_config["endpoint"].remove("qdrant://")
