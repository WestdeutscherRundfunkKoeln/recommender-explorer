import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from hashlib import sha256
from typing import Annotated

from envyaml import EnvYAML
from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, Header
from fastapi.exceptions import HTTPException
from google.cloud import storage
from pydantic import ValidationError
from src.bulk import bulk_ingest
from src.clients import SearchServiceClient
from src.maintenance import task_cleaner, reembedding_background_task
from src.models import (
    FullLoadRequest,
    FullLoadResponse,
    OpenSearchResponse,
    SingleTaskResponse,
    StorageChangeEvent,
    TasksResponse,
)
from src.preprocess_data import DataPreprocessor
from src.storage import download_document, get_storage_client
from src.task_status import TaskStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


NAMESPACE = "ingest"
EVENT_TYPE_DELETE = "OBJECT_DELETE"

CONFIG_PATH = os.environ.get("CONFIG_FILE", default="config.yaml")
STORAGE_SERVICE_ACCOUNT = os.environ.get("STORAGE_SERVICE_ACCOUNT", default="")
TASK_CLEANER_INTERVAL_SECONDS = float(
    os.environ.get(
        "TASK_CLEANER_INTERVAL_SECONDS",
        60 * 60 * 24,  # 24 hours
    )
)
REEMBED_INTERVAL_SECONDS = float(
    os.environ.get(
        "REEMBED_INTERVAL_SECONDS",
        60,  # 1 minute
    )
)

config = EnvYAML(CONFIG_PATH)
API_PREFIX = config.get("API_PREFIX", "")
ROUTER_PREFIX = os.path.join(API_PREFIX, NAMESPACE) if API_PREFIX else ""
HASH_FIELD = "embedTextHash"

data_preprocessor = DataPreprocessor(config)
search_service_client = SearchServiceClient.from_config(config)

maintenance_tasks = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    maintenance_tasks.add(
        asyncio.create_task(task_cleaner(TASK_CLEANER_INTERVAL_SECONDS))
    )
    maintenance_tasks.add(
        asyncio.create_task(
            reembedding_background_task(
                interval_seconds=REEMBED_INTERVAL_SECONDS,
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
    storage: Annotated[storage.Client, Depends(get_storage_client)],
    event: StorageChangeEvent,
    event_type: Annotated[str, Header(alias="eventType")],
):
    if event_type == EVENT_TYPE_DELETE:
        return search_service_client.delete(event.blob_id)

    document = download_document(storage, event)
    try:
        document = data_preprocessor.map_data(document)
    except ValidationError as exc:
        logger.error("Validation error: %s", str(exc))
        raise HTTPException(status_code=422, detail=str(exc))

    upsert_response = search_service_client.create_single_document(
        document.id, document.model_dump()
    )

    if not document.embedText:
        return upsert_response

    embed_hash_in_oss = search_service_client.get(document.id, [HASH_FIELD]).get(
        HASH_FIELD
    )
    embed_hash = sha256(document.embedText.encode("utf-8")).hexdigest()

    if (embed_hash_in_oss is None) or (embed_hash_in_oss != embed_hash):
        data_preprocessor.add_embeddings(document)

    return upsert_response  # TODO: check for meaningful return object. kept for backward compatibility?


@router.post("/ingest-multiple-items", status_code=202)
def ingest_multiple_items(
    body: FullLoadRequest,
    storage: Annotated[storage.Client, Depends(get_storage_client)],
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


app = FastAPI(title="Ingest Service")
app.include_router(router, prefix=ROUTER_PREFIX)
