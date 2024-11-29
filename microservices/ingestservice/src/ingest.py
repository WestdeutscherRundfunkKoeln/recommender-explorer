import itertools
import json
import logging
from hashlib import sha256
from typing import Iterable

from dto.recoexplorer_item import RecoExplorerItem
from google.api_core.exceptions import GoogleAPICallError
from google.cloud import storage
from google.cloud.storage.blob import Blob
from pydantic import ValidationError
from src.clients import SearchServiceClient
from src.log_handler import TaskLogHandler
from src.models import BulkIngestTaskStatus, StorageChangeEvent
from src.preprocess_data import DataPreprocessor
from src.task_status import TaskStatus

logger = logging.getLogger(__name__)
handler = TaskLogHandler()
handler.setLevel(logging.ERROR)
logger.addHandler(handler)

HASH_FIELD = "embedTextHash"
CHUNKSIZE = 50


def process_upsert_event(
    event: StorageChangeEvent,
    search_service_client: SearchServiceClient,
    storage: storage.Client,
    data_preprocessor: DataPreprocessor,
) -> dict:
    document = None
    try:
        blob = storage.bucket(event.bucket).blob(event.name)
        document = get_document_from_blob(
            blob, data_preprocessor, search_service_client
        )
        upsert_response = search_service_client.create_single_document(
            document.externalid, document.model_dump()
        )

        return upsert_response  # TODO: check for meaningful return object. still kept for backward compatibility?
    except Exception:
        if document:
            logger.info(
                "Exception when ingesting item %s:", document.externalid, exc_info=True
            )
        else:
            logger.info("Exception when ingesting item", exc_info=True)
        raise


def full_ingest(
    bucket: storage.Bucket,
    data_preprocessor: DataPreprocessor,
    search_service_client: SearchServiceClient,
    prefix: str,
    task_id: str,
    log_bucket: storage.Bucket,
) -> None:
    with TaskStatus(task_id, log_bucket) as task_status:
        bulk_ingest(
            blobs=iter(bucket.list_blobs(match_glob=f"{prefix}*.json")),
            data_preprocessor=data_preprocessor,
            search_service_client=search_service_client,
            task_status=task_status,
        )


def delta_ingest(
    bucket: storage.Bucket,
    data_preprocessor: DataPreprocessor,
    search_service_client: SearchServiceClient,
    prefix: str,
    task_id: str,
    log_bucket: storage.Bucket,
) -> None:
    with TaskStatus(task_id, log_bucket) as task_status:
        blobs = bucket.list_blobs(match_glob=f"{prefix}*.json")
        documents = [
            doc["_id"]
            for doc in search_service_client.scan(
                {"_source": False, "query": {"match_all": {}}}
            )
        ]
        delta = [
            blob
            for blob in blobs
            if blob.name.removeprefix(prefix).removesuffix(".json") not in documents
        ]
        bulk_ingest(
            blobs=iter(delta),
            data_preprocessor=data_preprocessor,
            search_service_client=search_service_client,
            task_status=task_status,
        )


def bulk_ingest(
    blobs: Iterable[Blob],
    data_preprocessor: DataPreprocessor,
    search_service_client: SearchServiceClient,
    task_status: TaskStatus,
) -> None:
    # iterator is consumed slice by slice
    while batch := list(itertools.islice(blobs, CHUNKSIZE)):
        upsert_batch(
            batch=batch,
            task_status=task_status,
            data_preprocessor=data_preprocessor,
            search_service_client=search_service_client,
        )
        logger.info("Uploaded %s items", len(batch))


def upsert_batch(
    batch: list[Blob],
    task_status: TaskStatus,
    data_preprocessor: DataPreprocessor,
    search_service_client: SearchServiceClient,
) -> None:
    task_status.set_status(BulkIngestTaskStatus.PREPROCESSING)
    items = {}
    for blob in batch:
        try:
            document = get_document_from_blob(
                blob=blob,
                data_preprocessor=data_preprocessor,
                task_status=task_status,
                search_service_client=search_service_client,
            )
        except (GoogleAPICallError, ValidationError, json.JSONDecodeError):
            continue
        items[document.externalid] = document.model_dump()

    task_status.set_status(BulkIngestTaskStatus.IN_FLIGHT)
    search_service_client.create_multiple_documents(items)
    logger.info("Uploaded items %s", list(items.keys()))
    task_status.increment_completed(len(items))
    task_status.increment_failed(len(batch) - len(items))


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


def delete_batch(
    bucket: storage.Bucket, prefix: str, search_service_client: SearchServiceClient
) -> None:
    try:
        ids_in_bucket = [
            blob.name.removeprefix(prefix).removesuffix(".json")
            for blob in bucket.list_blobs(match_glob=f"{prefix}*.json")
        ]
        ids_in_oss = [
            doc["_id"]
            for doc in search_service_client.scan(
                {"_source": False, "query": {"match_all": {}}}
            )
        ]
        delta = [id for id in ids_in_oss if id not in ids_in_bucket]
        search_service_client.delete_multiple_documents(delta)
        logger.info("Deleted items %s", delta)
    except Exception:
        logger.error("Error during delete batch", exc_info=True)
