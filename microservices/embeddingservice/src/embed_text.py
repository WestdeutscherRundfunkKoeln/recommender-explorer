import json
import logging
from hashlib import sha256
from typing import cast

import httpx
from numpy import ndarray
from sentence_transformers import SentenceTransformer
import shutil
import tempfile
from google.cloud import storage
import pathlib

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


def download_model(bucket_name: str, gs_path: str) -> SentenceTransformer | None:
    """Creats a temp directory and download the model to it. Synchronize download between processces via FileLock."""

    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    if gs_path not in [blob.name for blob in bucket.list_blobs()]:
        return None

    with tempfile.TemporaryDirectory() as temp_path:
        local_path = pathlib.Path(temp_path)
        zip_path = local_path / f"{gs_path}.zip"
        model_path = local_path / gs_path
        blob = bucket.blob(gs_path)
        logging.info(f"model {model_path} download started")
        blob.download_to_filename(zip_path)
        logging.info(f"model {model_path} download complete -> unpacking...")
        shutil.unpack_archive(zip_path, model_path)
        logging.info(f"Download model {gs_path} to {model_path} -> sucessfull")
    return SentenceTransformer(model_path.absolute().as_posix(), device="cpu")


class EmbedText:
    def __init__(self, config):
        self.config = config
        self.models = {}
        for model in self.config["models"]:
            for model_name, model_path in model.items():
                model = download_model(
                    bucket_name=self.config["bucket_name"],
                    gs_path=model_path,
                )
                self.models[model_name] = (
                    model
                    if model is not None
                    else SentenceTransformer(model_path, device="cpu")
                )

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
