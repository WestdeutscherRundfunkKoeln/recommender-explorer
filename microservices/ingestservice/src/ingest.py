import json
import logging

from google.api_core.exceptions import GoogleAPICallError
from google.cloud.storage.blob import Blob
from hashlib import sha256
from pydantic import ValidationError

from dto.recoexplorer_item import RecoExplorerItem
from src.preprocess_data import DataPreprocessor
from src.clients import SearchServiceClient

logger = logging.getLogger(__name__)

HASH_FIELD = "embedTextHash"


def get_document_from_blob(
    blob: Blob,
    data_preprocessor: DataPreprocessor,
    search_service_client: SearchServiceClient,
) -> RecoExplorerItem:
    try:
        document = blob.download_as_text()
    except GoogleAPICallError:
        logger.error("Error downloading %s", blob.name, exc_info=True)
        raise

    try:
        document = json.loads(document)
    except json.JSONDecodeError:
        logger.error("File %s is not a valid json", blob.name, exc_info=True)
        raise

    try:
        document = data_preprocessor.map_data(document)
    except ValidationError:
        logger.error("Validation error", exc_info=True)
        raise

    try:
        reference_hash = search_service_client.get(
            document.externalid, [HASH_FIELD]
        ).get(HASH_FIELD)
    except Exception:
        reference_hash = None
        logger.error("Unexpected error fetching EmbedHash", exc_info=True)

    incoming_hash = sha256(document.embedText.encode("utf-8")).hexdigest()

    if incoming_hash == reference_hash:
        document.needs_reembedding = False

    return document
