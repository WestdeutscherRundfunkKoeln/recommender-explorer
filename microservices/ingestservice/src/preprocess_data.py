from dto.recoexplorer_item import RecoExplorerItem
from fastapi import HTTPException
from pydantic import ValidationError
import logging
import json
import pyjq
import httpx

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


class DataPreprocessor:
    def __init__(self, config):
        self.mapping = config["mapping_definition"]
        self.base_url_embedding = config["base_url_embedding"]
        self.api_key = config["api_key"]

    def map_data(self, data: dict) -> RecoExplorerItem:  # input = entity
        mapped_data = pyjq.one(self.mapping, data)
        logger.debug("Mapped data: " + json.dumps(mapped_data, indent=4, default=str))
        response = RecoExplorerItem.model_validate(mapped_data)
        return response

    def add_embeddings(self, mapped_data: RecoExplorerItem):
        # Hint: Transformed to fire and forget request
        try:
            httpx.post(
                f"{self.base_url_embedding}/add-embedding-to-doc",
                json={
                    "id": mapped_data.id,
                    "embedText": mapped_data.embedText,
                },
                timeout=20.0,
                headers={"x-api-key": self.api_key},
            )
        except httpx.ReadTimeout:
            pass
