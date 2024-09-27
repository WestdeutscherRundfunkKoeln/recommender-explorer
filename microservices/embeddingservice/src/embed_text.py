import json
import logging
import os
import pathlib
import shutil
from hashlib import sha256
from typing import cast

import httpx
from google.cloud import storage
from google.oauth2 import service_account
from numpy import ndarray
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


def download_model(
    bucket: storage.Bucket,
    model_zip: str,
    local_path: str,
) -> None:
    """Creats a temp directory and download the model to it. Synchronize download between processces via FileLock."""
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


class EmbedText:
    def __init__(self, config):
        self.config = config
        self.models = {}
        bucket = None
        if "service_account" in self.config:
            credentials = service_account.Credentials.from_service_account_info(
                self.config["service_account"]
            )
            client = storage.Client(credentials=credentials)
            bucket = client.bucket(self.config["bucket_name"])
        for model in self.config["models"]:
            for model_name, model_path in model.items():
                bucket_path = (
                    f'{self.config["bucket_path"]}/{model_path.split("/")[-1]}.zip'
                )
                local_path = (
                    (pathlib.Path(config["local_model_path"]) / bucket_path)
                    .as_posix()
                    .split(".")[0]
                )
                if not os.path.exists(local_path):
                    logger.info("Model %s not found at %s", model_path, local_path)
                    if bucket:
                        download_model(
                            bucket=bucket,
                            model_zip=bucket_path,
                            local_path=local_path,
                        )
                load_path = local_path if os.path.exists(local_path) else model_path

                self.models[model_name] = SentenceTransformer(
                    load_path,
                    device="cpu",
                    cache_folder=config["local_model_path"],
                    trust_remote_code=True,
                )

    def embed_text(self, embed_text: str, models_to_use: list[str] | None):
        response: dict[str, str | list[float]] = {
            "embedTextHash": sha256(embed_text.encode("utf-8")).hexdigest()
        }

        if not models_to_use:
            models_to_use = list(self.models.keys())

        for model in models_to_use:
            if model in self.models:
                logger.info("Embedding text with model %s", model)
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
            url=f"{self.config.get('base_url_search')}/documents/{id}",
            json=embedding,
            headers={"x-api-key": self.config["api_key"]},
        )
