import logging
import json
from sentence_transformers import SentenceTransformer
from hashlib import sha256
import os
import httpx

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

BASE_URL_SEARCH = os.environ.get("BASE_URL_SEARCH", default="")


class EmbedText:
    def __init__(self, config):
        self.config = config

    def embed_text(self, embed_text):
        hash = sha256(embed_text.encode("utf-8")).hexdigest()
        response: dict[str, str | list[float]] = {"embedTextHash": hash}

        for model in self.config["models"]:
            for model_name, model_path in model.items():
                self.model = SentenceTransformer(model_path)
                embedding = self.model.encode(embed_text).tolist()
                response[model_name] = embedding

        logger.info("Response: " + json.dumps(response, indent=4, default=str))

        return response

    def add_embedding_to_document(self, id, embedding):
        embedding["id"] = id
        # Send request to search service to add embedding to index
        httpx.post(
            url=f"{BASE_URL_SEARCH}/create-single-document",
            json=embedding,
            headers={"x-api-key": self.config.get("api_key")},
        ).json()
