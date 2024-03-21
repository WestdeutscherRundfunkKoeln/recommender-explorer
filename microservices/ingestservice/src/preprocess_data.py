from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from envyaml import EnvYAML
from dto.recoexplorer_item import RecoExplorerItem
import logging
import json
import pyjq
import os
import httpx

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

URL_EMBEDDING = os.environ.get("URL_EMBEDDING")


class DataPreprocessor:

    def __init__(self, config):
        mapping_definition_file = config['mapping_definition_file']
        mapping_file = EnvYAML(mapping_definition_file)
        self.mapping = mapping_file['mapping']

    def preprocess_data(self, data):
        # map data
        try:
            mapped_data = self.map_data(data).model_dump_json()  # TODO: Find out what causes triple quotation marks in long description and fix it
        except ValidationError as exc:
            error_message = repr(exc.errors()[0]['type'])
            raise HTTPException(status_code=422, detail=error_message)
        preprocessed_data = json.loads(mapped_data)
        self.add_embeddings(preprocessed_data)
        return preprocessed_data

    def map_data(self, data) -> RecoExplorerItem: # input = entity
        mapped_data = pyjq.one(self.mapping, data)
        logger.info('Mapped data: ' + json.dumps(mapped_data, indent=4, default=str))
        response = RecoExplorerItem.model_validate(mapped_data)
        return response

    def add_embeddings(self, mapped_data): # TODO: Make this asynchronous
        # get embedding
        request_payload = {"id": mapped_data["id"],
                           "embedText": mapped_data["embedText"]}
        httpx.post(URL_EMBEDDING, json=request_payload).json()
        # mapped_data.update(embedding_response)
        return mapped_data
