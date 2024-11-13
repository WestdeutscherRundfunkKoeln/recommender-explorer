import asyncio
import traceback
from datetime import datetime
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from hashlib import sha256
from typing import Annotated

from envyaml import EnvYAML
from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, Header, Request
from fastapi.exceptions import HTTPException
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from pydantic import ValidationError
from src.bulk import bulk_ingest
from src.clients import SearchServiceClient
from src.maintenance import reembedding_background_task, task_cleaner
from src.models import (
    FullLoadRequest,
    FullLoadResponse,
    OpenSearchResponse,
    SingleTaskResponse,
    StorageChangeEvent,
    TasksResponse,
)
from src.preprocess_data import DataPreprocessor
from src.storage import download_document, StorageClientFactory
from src.task_status import TaskStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


NAMESPACE = "ingest"
EVENT_TYPE_DELETE = "OBJECT_DELETE"

CONFIG_PATH = os.environ.get("CONFIG_FILE", default="config.yaml")

config = EnvYAML(CONFIG_PATH)
API_PREFIX = config.get("api_prefix", "")
ROUTER_PREFIX = os.path.join(API_PREFIX, NAMESPACE) if API_PREFIX else ""
HASH_FIELD = "embedTextHash"

storage_client_factory = StorageClientFactory.from_config(config)
data_preprocessor = DataPreprocessor(config)
search_service_client = SearchServiceClient.from_config(config)

maintenance_tasks = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    maintenance_tasks.add(
        asyncio.create_task(task_cleaner(config["task_cleaner_interval_seconds"]))
    )
    maintenance_tasks.add(
        asyncio.create_task(
            reembedding_background_task(
                interval_seconds=config["reembed_interval_seconds"],
                search_service_client=search_service_client,
                config=config,
            )
        )
    )
    yield
    search_service_client.close()


router = APIRouter()


@router.get("/health-check")
def health_check():
    return {"status": "OK"}


@router.post("/events", response_model=OpenSearchResponse)
def ingest_item(
    storage: Annotated[storage.Client, Depends(storage_client_factory)],
    event: StorageChangeEvent,
    event_type: Annotated[str, Header(alias="eventType")],
    request: Request,
):
    document = None
    try:
        if event_type == EVENT_TYPE_DELETE:
            return search_service_client.delete(event.blob_id)

        document = download_document(storage, event)
        try:
            document = data_preprocessor.map_data(document)
        except ValidationError as exc:
            logger.error("Validation error: %s", str(exc))
            raise

        # Check for EmbedHash in OSS
        try:
            embed_hash_in_oss = search_service_client.get(
                document.externalid, [HASH_FIELD]
            ).get(HASH_FIELD)
        except Exception as exc:
            embed_hash_in_oss = None
            logger.error("Unexpected error fetching EmbedHash: %s", str(exc))

        # Get EmbedHash of the document
        embed_hash = sha256(document.embedText.encode("utf-8")).hexdigest()

        # Compare EmbedHashes and set needs_reembedding flag
        if (embed_hash_in_oss is None) or (embed_hash_in_oss != embed_hash):
            document.needs_reembedding = True
        else:
            document.needs_reembedding = False

        # Send document to search service
        upsert_response = search_service_client.create_single_document(
            document.externalid, document.model_dump()
        )

        return upsert_response  # TODO: check for meaningful return object. still kept for backward compatibility?
    except Exception as e:
        exception_traceback = traceback.format_exc()
        _log_exception_traceback(document, e, exception_traceback)
        ts = datetime.now().isoformat()
        data = event.model_dump()
        data["event_type"] = event_type
        data["timestamp"] = ts
        data["exception"] = str(e)
        data["url"] = str(request.url)
        try:
            storage.bucket(config["dead_letter_bucket"]).blob(
                f"{ts}.json"
            ).upload_from_string(json.dumps(data))
        except GoogleCloudError:
            logger.error("Error during upload of log file", exc_info=True)
        raise HTTPException(status_code=200, detail=str(e))


@router.post("/ingest-multiple-items", status_code=202)
def ingest_multiple_items(
    body: FullLoadRequest,
    storage: Annotated[storage.Client, Depends(storage_client_factory)],
    tasks: BackgroundTasks,
) -> FullLoadResponse:
    task_id = str(uuid.uuid4())
    tasks.add_task(
        bulk_ingest,
        config=config,
        bucket=storage.bucket(body.bucket),
        data_preprocessor=data_preprocessor,
        search_service_client=search_service_client,
        prefix=body.prefix,
        task_id=task_id,
    )
    return FullLoadResponse(task_id=task_id)


@router.get("/tasks/{task_id}")
def get_task(task_id: str) -> SingleTaskResponse:
    task = TaskStatus.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return SingleTaskResponse(task=task)


@router.get("/tasks")
def get_tasks() -> TasksResponse:
    tasks = TaskStatus.get_tasks()
    return TasksResponse(tasks=tasks.values())


def _log_exception_traceback(document, e, exception_traceback):
    document_id = getattr(document, "externalid", None)
    if document_id:
        logger.info(
            f"Exception when ingesting item {document_id}: {str(e)}\nTraceback: {exception_traceback}"
        )
    else:
        logger.info(
            f"Exception when ingesting item: {str(e)}\nTraceback: {exception_traceback}"
        )

# main app
app = FastAPI(title="Ingest Service", lifespan=lifespan)
app.include_router(router, prefix=ROUTER_PREFIX)
