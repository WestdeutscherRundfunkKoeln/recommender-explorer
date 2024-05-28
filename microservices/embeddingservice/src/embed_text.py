import logging
import json
from sentence_transformers import SentenceTransformer
from hashlib import sha256
import os
import httpx

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

#TODO: use config instead of accessing env var directly!
BASE_URL_SEARCH = os.environ.get("BASE_URL_SEARCH", default="")


class EmbedText:
    def __init__(self, config):
        self.config = config
        self.models = {}
        self.configured_models = []
        for model in self.config["models"]:
            for model_name, model_path in model.items():
                self.models[model_name] = SentenceTransformer(model_path, device='cpu')
                self.configured_models.append(model_name)

    def embed_text(self, embed_text:str, models_to_use:list[str]):
        hash = sha256(embed_text.encode("utf-8")).hexdigest()
        response: dict[str, str | list[float]] = {"embedTextHash": hash}

        # filter available models by parameter selection
        if models_to_use == [] or models_to_use is None:
            # backward compat, if param omiited use all models in config
            calc_models = self.configured_models
            unknown_models = []
        else:
            # we have a model selection, check what can be fullfilled and what not
            known_models =  list(set(models_to_use) & set(self.configured_models))
            if len(known_models) < len(models_to_use):
                # there are models we don't know about, handle gracefully
                unknown_models = list(set(models_to_use) - set(self.configured_models))
                logger.warn(f'The models {unknown_models} are not known in service config!')
                calc_models = known_models
            else:
                # we can calculate all models, nice
                unknown_models = []
                calc_models = known_models

        for model in unknown_models:
            response[model] = 'unknown model!'
        for model in calc_models:
            embedding = self.models[model].encode(embed_text).tolist()
            response[model] = embedding
        


        logger.debug("Response: " + json.dumps(response, indent=4, default=str))

        return response

    def add_embedding_to_document(self, id, embedding):
        embedding["id"] = id
        # Send request to search service to add embedding to index
        httpx.post(
            url=f"{BASE_URL_SEARCH}/create-single-document",
            json=embedding,
            headers={"x-api-key": self.config["api_key"]},
        ).json()
