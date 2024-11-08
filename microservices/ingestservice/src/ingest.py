import itertools
import json
import logging
from hashlib import sha256

import httpx
from dto.recoexplorer_item import RecoExplorerItem
from envyaml import EnvYAML
from google.api_core.exceptions import GoogleAPICallError
from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.cloud.storage.blob import Blob
from pydantic import ValidationError

from src.clients import SearchServiceClient
from src.log_handler import TaskLogHandler
from src.models import BulkIngestTaskStatus
from src.preprocess_data import DataPreprocessor
from src.task_status import TaskStatus

logger = logging.getLogger(__name__)
handler = TaskLogHandler()
handler.setLevel(logging.ERROR)
logger.addHandler(handler)

HASH_FIELD = "embedTextHash"
CHUNKSIZE = 50


def get_document_from_blob(
    blob: Blob,
    data_preprocessor: DataPreprocessor,
    search_service_client: SearchServiceClient,
    task_status: TaskStatus | None = None,
) -> RecoExplorerItem:
    try:
        document = blob.download_as_text()
    except GoogleAPICallError:
        logger.error(
            "Error downloading %s",
            blob.name,
            exc_info=True,
            extra={"task": task_status},
        )
        raise

    try:
        document = json.loads(document)
    except json.JSONDecodeError:
        logger.error(
            "File %s is not a valid json",
            blob.name,
            exc_info=True,
            extra={"task": task_status},
        )
        raise

    try:
        document = data_preprocessor.map_data(document)
    except ValidationError:
        logger.error("Validation error", exc_info=True, extra={"task": task_status})
        raise

    reference_hash = None
    try:
        reference_hash = search_service_client.get(
            document.externalid, [HASH_FIELD]
        ).get(HASH_FIELD)
    except Exception:  # TODO: specify exception
        logger.error("Unexpected error fetching EmbedHash", exc_info=True)

    incoming_hash = sha256(document.embedText.encode("utf-8")).hexdigest()

    if incoming_hash == reference_hash:
        document.needs_reembedding = False

    return document


def bulk_ingest(
    bucket: storage.Bucket,
    data_preprocessor: DataPreprocessor,
    search_service_client: SearchServiceClient,
    prefix: str,
    task_id: str,
):
    logger.info("Starting bulk ingest")
    task_status = TaskStatus.spawn(id=task_id)
    try:
        batch_start = 1
        batch_end = 0
        blobs = list(bucket.list_blobs(match_glob=f"{prefix}*.json"))
        blobs_iter = iter(blobs)
        # iterator is consumed slice by slice
        while batch := list(itertools.islice(blobs_iter, CHUNKSIZE)):
            batch_end = upsert_batch(
                batch=batch,
                task_status=task_status,
                element_counter=batch_start,
                data_preprocessor=data_preprocessor,
                search_service_client=search_service_client,
            )
            logger.info("Uploaded items %s to %s", batch_start, batch_end)
            batch_start = batch_end + 1

        task_status.set_status(BulkIngestTaskStatus.COMPLETED)
    except Exception as e:
        logger.error("Error during bulk ingest", exc_info=True)
        task_status.add_error(str(e))
        task_status.set_status(BulkIngestTaskStatus.FAILED)


def upsert_batch(
    batch: list[Blob],
    task_status: TaskStatus,
    element_counter: int,
    data_preprocessor: DataPreprocessor,
    search_service_client: SearchServiceClient,
) -> int:
    task_status.set_status(BulkIngestTaskStatus.PREPROCESSING)
    item_dict = {}
    for blob in batch:
        element_counter += 1
        try:
            document = get_document_from_blob(
                blob=blob,
                data_preprocessor=data_preprocessor,
                task_status=task_status,
                search_service_client=search_service_client,
            )
        except (GoogleAPICallError, ValidationError, json.JSONDecodeError):
            continue
        item_dict[document.externalid] = document.model_dump()

    task_status.set_status(BulkIngestTaskStatus.IN_FLIGHT)
    search_service_client.create_multiple_documents(item_dict)
    return element_counter
