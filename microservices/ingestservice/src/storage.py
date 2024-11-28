import logging
import os
from typing import Any

from envyaml import EnvYAML
from google.auth.credentials import AnonymousCredentials
from google.cloud import storage
from google.oauth2 import service_account

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
            logger.info("Using storage emulator")
            return storage.Client(project="test", credentials=AnonymousCredentials())

        credentials = service_account.Credentials.from_service_account_info(
            self.storage_service_account
        )
        return storage.Client(credentials=credentials)
