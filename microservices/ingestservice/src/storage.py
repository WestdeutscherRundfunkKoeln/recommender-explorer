import json
import logging
import os
from typing import Any

from envyaml import EnvYAML
from fastapi.exceptions import HTTPException
from google.api_core.exceptions import GoogleAPICallError
from google.cloud import storage
from google.oauth2 import service_account
from google.auth.credentials import AnonymousCredentials
from fastapi.exceptions import HTTPException
from src.models import StorageChangeEvent

logger = logging.getLogger(__name__)


class StorageClientFactory:
    def __init__(
        self,
        storage_service_account: dict[str, Any],
        gcs_url: str = "http://localhost:4443",
    ):
        self.storage_service_account = storage_service_account
        self.gcs_url = gcs_url

    @classmethod
    def from_config(cls, config: EnvYAML) -> "StorageClientFactory":
        return cls(config["storage_service_account"], config["gcs_url"])

    def __call__(self) -> storage.Client:
        if not self.storage_service_account:
            os.environ.setdefault("STORAGE_EMULATOR_HOST", f"{self.gcs_url}:4443")
            return storage.Client(project="test", credentials=AnonymousCredentials())

        credentials = service_account.Credentials.from_service_account_info(
            self.storage_service_account
        )
        return storage.Client(credentials=credentials)


def download_document(
    storage: storage.Client,
    event: StorageChangeEvent,
) -> dict:
    blob = storage.bucket(event.bucket).blob(event.name)
    try:
        raw_document = blob.download_as_text()
    except GoogleAPICallError as e:
        logger.error("Error during download of file %s", event.name, exc_info=True)
        status_code = e.code if e.code else 400
        raise HTTPException(status_code=status_code, detail=e.message)

    try:
        document_json = json.loads(raw_document)
    except json.JSONDecodeError as e:
        logger.error("File %s is not a valid json", event.name, exc_info=True)
        raise HTTPException(status_code=422, detail=e.msg)
    return document_json
