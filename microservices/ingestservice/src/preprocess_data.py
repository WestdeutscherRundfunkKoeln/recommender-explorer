import json
import logging

import httpx
import pyjq
from dto.recoexplorer_item import RecoExplorerItem
from fastapi import HTTPException
from pydantic import ValidationError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


class DataPreprocessor:
    def __init__(self, config):
        self.mapping = config["mapping_definition"]
        self.base_url_embedding = config["base_url_embedding"]
        self.api_key = config["api_key"]

    def preprocess_data(self, data: dict) -> RecoExplorerItem:
        # map data
        try:
            # TODO: Find out what causes triple quotation marks in long description and fix it
            preprocessed_data = self.map_data(data)
        except ValidationError as exc:
            logger.error("Validation error: " + repr(exc.errors()))
            error_message = repr(exc.errors()[0]["type"])
            raise HTTPException(status_code=422, detail=error_message)
        return preprocessed_data

    def map_data(self, data: dict) -> RecoExplorerItem:  # input = entity
        mapped_data = pyjq.one(self.mapping, data)
        logger.info("Mapped data: " + json.dumps(mapped_data, indent=4, default=str))
        response = RecoExplorerItem.model_validate(mapped_data)
        return response

    def add_embeddings(self, mapped_data):  # TODO: Make this asynchronous
        # get embedding
        request_payload = {
            "id": mapped_data.id,
            "embedText": mapped_data.embedText,
        }
        httpx.post(
            f"{self.base_url_embedding}/add-embedding-to-doc",
            json=request_payload,
            timeout=None,
            headers={"x-api-key": self.api_key},
        ).json()
