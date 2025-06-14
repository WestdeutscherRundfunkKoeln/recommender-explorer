import json
import logging
import os
import pathlib
import shutil
import datetime
from hashlib import sha256
from typing import cast

import httpx
from google.cloud import storage
from google.oauth2 import service_account
from numpy import ndarray
from sentence_transformers import SentenceTransformer
import re

from src.constants import (
    MODELS_KEY,
    C2C_MODELS_KEY,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


def download_model(
        bucket: storage.Bucket,
        model_zip: str,
        local_path: str,
) -> None:
    """
    Creates a temp directory and download the model to it.
    Synchronize download between processes via FileLock.
    """
    if model_zip not in [blob.name for blob in bucket.list_blobs()]:
        logger.info("Model %s not found in bucket.", model_zip)
        return

    zip_path = pathlib.Path(f"{local_path}.zip")

    if not os.path.exists(zip_path.parent):
        os.makedirs(zip_path.parent)

    blob = bucket.blob(model_zip)
    logging.info("model %s download started", model_zip)
    blob.download_to_filename(zip_path)
    logging.info("model %s download complete -> unpacking...", model_zip)
    shutil.unpack_archive(zip_path, local_path)
    logging.info("Download model %s to %s -> sucessfull", model_zip, local_path)

def cut_to_full_sentence(
        text: str,
) -> str:
    """
    Cut off the text at the last full sentence.
    """
    match = re.search(r'[\.!?](?!.*[\.!?])', text)
    return text[:match.end()].strip() if match else text.strip()

class EmbedText:
    def __init__(self, config):
        """
        Initialize the EmbedText class.

        :param config: The full configuration dictionary.
        :param key: The key under which the model configurations are stored (e.g., 'wdr', 'br').
                    If no key is provided, all models across all keys will be loaded.
        """
        self.config = config
        self.model_configs = {}
        self.models = {}
        self.bucket = None
        self.models_max_length = {}

        # Initialize the bucket for downloading models, if needed
        if sa := self.config.get("service_account"):
            credentials = service_account.Credentials.from_service_account_info(sa)
            client = storage.Client(credentials=credentials)
            self.bucket = client.bucket(self.config["bucket_name"])

        self.load_all_models()

    def load_all_models(self):
        """
        Load all models from all keys, ignoring any specific key.
        """
        logger.info("Loading all models across all keys")

        for key, configuration in self.config[MODELS_KEY].items():
            if C2C_MODELS_KEY in configuration:
                self.model_configs.update(configuration[C2C_MODELS_KEY])

        for model, model_config in self.model_configs.items():
            if not model_config.get("model_path"):
                continue

            bucket_path = f'{self.config["bucket_path"]}/{model_config["model_path"].split("/")[-1]}.zip'
            local_path = (
                (pathlib.Path(self.config["local_model_path"]) / bucket_path)
                .as_posix()
                .split(".")[0]
            )
            if not os.path.exists(local_path):
                logger.info(
                    "Model %s not found at %s",
                    model_config["model_path"],
                    local_path,
                )
                if self.bucket:
                    download_model(
                        bucket=self.bucket,
                        model_zip=bucket_path,
                        local_path=local_path,
                    )
            load_path = (
                local_path
                if os.path.exists(local_path)
                else model_config["model_path"]
            )

            self.models[model_config["model_name"]] = SentenceTransformer(
                load_path,
                device="cpu",
                cache_folder=self.config["local_model_path"],
                trust_remote_code=True,
            )

            self.models_max_length[model_config["model_name"]] = self.models[model_config["model_name"]].tokenizer.model_max_length


    def embed_text(self, embed_text: str, models_to_use: list[str] | None, return_embed_text = False):
        response: dict[str, str | list[float]] = {
            "embedTextHash": sha256(embed_text.encode("utf-8")).hexdigest()
        }

        if not models_to_use:
            models_to_use = list(self.models.keys())

        for model in models_to_use:
            if model in self.models:
                logger.info("Embedding text with model %s", model)
                start_encode = datetime.datetime.now()
                
                if return_embed_text:
                    response[model] = dict()
                    response[model]["embedded_text"] = cut_to_full_sentence(
                            self.models[model].tokenizer.decode(
                                self.models[model].tokenizer(
                                    embed_text,
                                    max_length=self.models_max_length[model],
                                    truncation=True,
                                    add_special_tokens=False
                                )['input_ids']
                            )
                        )
                    response[model]["embedding"] = cast(
                        ndarray, self.models[model].encode(embed_text)
                    ).tolist()
                else:
                    response[model] = cast(
                        ndarray, self.models[model].encode(embed_text)
                    ).tolist()

                end_encode = datetime.datetime.now()
                call_duration_encode = (
                    end_encode - start_encode
                ).total_seconds() * 1000
                logger.info(f"Embedding took {call_duration_encode} ms -> succesfull")
                continue
            response[model] = "unknown model!"
            logger.warning("The model '%s' is not known in service config!", model)

        logger.info("Response: %s", json.dumps(response, indent=4, default=str))

        return response

    def add_embedding_to_document(self, id, embedding):
        embedding["needs_reembedding"] = False

        # Send request to search service to add embedding to index
        logger.info(
            "Calling search service to add embedding with id ["
            + str(id)
            + "] to document"
        )
        httpx.post(
            url=f"{self.config.get('base_url_search')}/documents/{id}",
            json=embedding,
            headers={"x-api-key": self.config["api_key"]},
        )