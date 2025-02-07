import itertools
import json
import logging

from google.cloud.storage.blob import Blob
import httpx
from envyaml import EnvYAML
from google.cloud import storage
from google.cloud.exceptions import NotFound
from pydantic import ValidationError
from src.log_handler import TaskLogHandler
from src.clients import SearchServiceClient
from src.models import BulkIngestTaskStatus
from src.preprocess_data import DataPreprocessor
from src.task_status import TaskStatus

CHUNKSIZE = 50
HASH_FIELD = "embedTextHash"

logger = logging.getLogger(__name__)
handler = TaskLogHandler()
handler.setLevel(logging.ERROR)
logger.addHandler(handler)


def bulk_ingest(
    config: EnvYAML,
    bucket: storage.Bucket,
    data_preprocessor: DataPreprocessor,
    search_service_client: SearchServiceClient,
    prefix: str,
    task_id: str,
):
    logger.info("Starting bulk ingest")
    task_status = TaskStatus.spawn(id=task_id)
    try:
        blobs = list(bucket.list_blobs(match_glob=f"{prefix}*.json"))
        blobs_iter = iter(blobs)
        # iterator is consumed slice by slice
        while batch := list(itertools.islice(blobs_iter, CHUNKSIZE)):
            upsert_batch(
                batch=batch,
                task_status=task_status,
                data_preprocessor=data_preprocessor,
                search_service_client=search_service_client,
                config=config,
            )
            logger.info("Uploaded %s items", len(batch))

        task_status.set_status(BulkIngestTaskStatus.COMPLETED)
    except Exception as e:
        logger.error("Error during bulk ingest", exc_info=True)
        task_status.add_error(str(e))
        task_status.set_status(BulkIngestTaskStatus.FAILED)


def upsert_batch(
    batch: list[Blob],
    task_status: TaskStatus,
    data_preprocessor: DataPreprocessor,
    search_service_client: SearchServiceClient,
    config: EnvYAML,
) -> None:
    task_status.set_status(BulkIngestTaskStatus.PREPROCESSING)
    item_dict = {}
    for blob in batch:
        mapped_data = read_data_and_embed(
            task_status=task_status,
            blob=blob,
            data_preprocessor=data_preprocessor,
            config=config,
        )
        if mapped_data is None:
            continue
        item_dict[mapped_data["externalid"]] = mapped_data

    task_status.set_status(BulkIngestTaskStatus.IN_FLIGHT)
    search_service_client.create_multiple_documents(item_dict)
    task_status.increment_completed(len(item_dict))
    task_status.increment_failed(len(batch) - len(item_dict))


def read_data_and_embed(
    task_status: TaskStatus,
    blob: Blob,
    data_preprocessor: DataPreprocessor,
    config: EnvYAML,
) -> dict | None:
    logger.info(f"Preprocessing {blob.name}")
    try:
        data = json.loads(
            blob.download_as_text()
        )  # TODO: add retry logic, see https://cloud.google.com/python/docs/reference/storage/latest/google.cloud.storage.blob.Blob#google_cloud_storage_blob_Blob_download_as_text
    except NotFound:
        logger.error(
            "Could not find file %s",
            blob.name,
            exc_info=True,
            extra={"task": task_status},
        )
        return

    try:
        mapped_data = data_preprocessor.map_data(data)
    except ValidationError:
        logger.error(
            "Error during preprocessing of file %s",
            blob.name,
            exc_info=True,
            extra={"task": task_status},
        )
        return

    # Trigger embedding service to add embeddings to index
    try:
        embeddings = httpx.post(
            f"{config.get('base_url_embedding', '')}/embedding",
            json={
                "embedText": mapped_data.embedText,
            },
            timeout=None,
            headers={"x-api-key": config["api_key"]},
        )
    except httpx.TimeoutException:
        logger.error(
            "Error during embedding calculation for file %s",
            blob.name,
            exc_info=True,
            extra={"task": task_status},
        )
        return

    if embeddings.status_code != 200:
        raise Exception(
            f"Error during embedding in embedding service for item {blob.name}"
        )
    return {**mapped_data.model_dump(), **embeddings.json()}
