import asyncio
import itertools
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from hashlib import sha256
from typing import Annotated, Any

import httpx
from envyaml import EnvYAML
from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, Header
from fastapi.exceptions import HTTPException
from google.api_core.exceptions import GoogleAPICallError
from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.oauth2 import service_account
from pydantic import ValidationError
from src.clients import SearchServiceClient
from src.models import (
    BulkIngestTaskStatus,
    FullLoadRequest,
    FullLoadResponse,
    OpenSearchResponse,
    SingleTaskResponse,
    StorageChangeEvent,
    TasksResponse,
)
from src.preprocess_data import DataPreprocessor
from src.task_status import TaskStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


NAMESPACE = "ingest"
EVENT_TYPE_DELETE = "OBJECT_DELETE"

CONFIG_PATH = os.environ.get("CONFIG_FILE", default="config.yaml")
STORAGE_SERVICE_ACCOUNT = os.environ.get("STORAGE_SERVICE_ACCOUNT", default="")

config = EnvYAML(CONFIG_PATH)
BASE_URL_EMBEDDING = config.get("base_url_embedding", "")
API_PREFIX = config.get("API_PREFIX", "")
ROUTER_PREFIX = os.path.join(API_PREFIX, NAMESPACE) if API_PREFIX else ""
CHUNKSIZE = 50

data_preprocessor = DataPreprocessor(config)
search_service_client = SearchServiceClient.from_config(config)


def request(data: dict[str, Any], url: str):
    # TODO: Remove timeout when search service is implemented
    return httpx.post(
        url, json=data, timeout=None, headers={"x-api-key": config["api_key"]}
    )


def get_storage_client():
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(STORAGE_SERVICE_ACCOUNT)
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    async def task_cleaner():
        while True:
            TaskStatus.clear()
            await asyncio.sleep(5 * 60)

    asyncio.create_task(task_cleaner())
    yield
    search_service_client.close()


router = APIRouter()


@router.get("/health-check")
def health_check():
    return {"status": "OK"}


@router.post("/events", response_model=OpenSearchResponse)
def ingest_item(
    storage: Annotated[storage.Client, Depends(get_storage_client)],
    event: StorageChangeEvent,
    event_type: Annotated[str, Header(alias="eventType")],
):
    if event_type == EVENT_TYPE_DELETE:
        id = event.name.split("/")[-1].split(".")[0]
        return search_service_client.delete(id)

    try:
        document = data_preprocessor.map_data(download_document(storage, event))
        # Add metadata to index
        upsert_response = search_service_client.create_single_document(
            document.model_dump()
        )

        if not document.embedText:
            return upsert_response

        embed_hash_in_oss = search_service_client.get(
            document.id, ["embedTextHash"]
        ).get("embedTextHash")
        embed_hash = sha256(document.embedText.encode("utf-8")).hexdigest()
        print(embed_hash_in_oss, embed_hash)

        if embed_hash_in_oss is not None and embed_hash_in_oss == embed_hash:
            return upsert_response

        # Trigger embedding service to add embeddings to index
        data_preprocessor.add_embeddings(document)
        return upsert_response  # TODO: check for meaningful return object. kept for backward compatibility?

    except ValidationError as exc:
        error_message = repr(exc.errors()[0]["type"])
        logger.error("Validation error: " + repr(exc.errors()))
        raise HTTPException(status_code=422, detail=error_message)


@router.post("/ingest-multiple-items", status_code=202)
def ingest_multiple_items(
    body: FullLoadRequest,
    storage: Annotated[storage.Client, Depends(get_storage_client)],
    tasks: BackgroundTasks,
) -> FullLoadResponse:
    task_id = str(uuid.uuid4())
    bucket = storage.bucket(body.bucket)
    tasks.add_task(bulk_ingest, bucket, body.prefix, task_id)
    return FullLoadResponse(task_id=task_id)


def bulk_ingest(
    bucket: storage.Bucket,
    prefix: str,
    task_id: str,
):
    logger.info("Starting bulk ingest")
    task_status = TaskStatus.spawn(id=task_id)
    try:
        blobs = list(bucket.list_blobs(match_glob=f"{prefix}*.json"))
        blobs_iter = iter(blobs)
        batch_start = 1
        batch_end = 0
        while batch := list(itertools.islice(blobs_iter, CHUNKSIZE)):
            task_status.set_status(BulkIngestTaskStatus.PREPROCESSING)
            item_dict = {}
            for blob in batch:
                batch_end += 1
                logger.info(f"Preprocessing {blob.name}")
                try:
                    data = json.loads(
                        blob.download_as_text()
                    )  # TODO: add retry logic, see https://cloud.google.com/python/docs/reference/storage/latest/google.cloud.storage.blob.Blob#google_cloud_storage_blob_Blob_download_as_text
                except NotFound as e:
                    logger.error("Could not load file: %s", blob.name, exc_info=True)
                    error_message = f"Could not load file {blob.name}: {str(e)}"
                    task_status.add_error(error_message)
                    continue

                try:
                    mapped_data = data_preprocessor.map_data(data)
                except ValidationError as e:
                    logger.error(
                        "Error during preprocessing of file %s",
                        blob.name,
                        exc_info=True,
                    )
                    error_message = f"An error occurred during preprocessing of item {blob.name}: {str(e)}"
                    task_status.add_error(error_message)
                    continue

                # Trigger embedding service to add embeddings to index
                try:
                    embeddings = request(
                        data={
                            "embedText": mapped_data.embedText,
                        },
                        url=f"{BASE_URL_EMBEDDING}/embedding",
                    )
                    if embeddings.status_code != 200:
                        raise Exception(
                            f"Error during embedding in embedding service for item {blob.name}"
                        )
                    mapped_data = {**mapped_data.model_dump(), **embeddings.json()}
                    item_dict[mapped_data["id"]] = mapped_data
                except httpx.TimeoutException as e:
                    logger.error(
                        "Error during embedding calculation for file %s",
                        blob.name,
                        exc_info=True,
                    )
                    error_message = f"An error occurred during embedding calculation for item {blob.name}: {str(e)}"
                    task_status.add_error(error_message)
                    continue

            task_status.set_status(BulkIngestTaskStatus.IN_FLIGHT)
            response = search_service_client.create_multiple_documents(item_dict)
            if response.status_code != 200:
                raise Exception(
                    f"Error during bulk ingest in search service: {response.status_code}"
                )
            logger.info("Uploaded items %s to %s", batch_start, batch_end)
            batch_start = batch_end + 1

        task_status.set_status(BulkIngestTaskStatus.COMPLETED)
    except Exception as e:
        logger.error("Error during bulk ingest", exc_info=True)
        task_status.add_error(str(e))
        task_status.set_status(BulkIngestTaskStatus.FAILED)


@router.get("/tasks/{task_id}")
def get_task(task_id: str) -> SingleTaskResponse:
    task = TaskStatus(task_id).get()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return SingleTaskResponse(task=task)


@router.get("/tasks")
def get_tasks() -> TasksResponse:
    tasks = TaskStatus.get_tasks()
    return TasksResponse(tasks=tasks.values())


app = FastAPI(title="Ingest Service")
app.include_router(router, prefix=ROUTER_PREFIX)
