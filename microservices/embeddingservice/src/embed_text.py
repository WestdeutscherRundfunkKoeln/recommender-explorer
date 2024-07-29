import json
import logging
from hashlib import sha256
from typing import cast

import httpx
from numpy import ndarray
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


class EmbedText:
    def __init__(self, config):
        self.config = config
        self.models = {
            model_name: SentenceTransformer(model_path, device="cpu")
            for model in self.config["models"]
            for model_name, model_path in model.items()
        }

    def embed_text(self, embed_text: str, models_to_use: list[str] | None):
        response: dict[str, str | list[float]] = {
            "embedTextHash": sha256(embed_text.encode("utf-8")).hexdigest()
        }

        if not models_to_use:
            models_to_use = list(self.models.keys())

        for model in models_to_use:
            if model in self.models:
                response[model] = cast(
                    ndarray, self.models[model].encode(embed_text)
                ).tolist()
                continue
            response[model] = "unknown model!"
            logger.warning("The model '%s' is not known in service config!", model)

        logger.debug("Response: %s", json.dumps(response, indent=4, default=str))

        return response

    def add_embedding_to_document(self, id, embedding):
        embedding["id"] = id
        # Send request to search service to add embedding to index
        httpx.post(
            url=f"{self.config.get('base_url_search')}/create-single-document",
            json=embedding,
            headers={"x-api-key": self.config["api_key"]},
        )
