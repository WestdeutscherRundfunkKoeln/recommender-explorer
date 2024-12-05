import asyncio
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

from envyaml import EnvYAML
from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, Header, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from httpx import HTTPStatusError
from src.clients import SearchServiceClient
from src.ingest import full_ingest, process_upsert_event
from src.maintenance import (
    delete_background_task,
    delta_load_background_task,
    reembedding_background_task,
    task_cleaner,
)
from src.models import (
    FullLoadRequest,
    FullLoadResponse,
    OpenSearchResponse,
    SingleTaskResponse,
    StorageChangeEvent,
    TasksResponse,
)
from src.preprocess_data import DataPreprocessor
from src.storage import StorageClientFactory
from src.task_status import TaskStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


NAMESPACE = "ingest"
EVENT_TYPE_DELETE = "OBJECT_DELETE"

CONFIG_PATH = os.environ.get("CONFIG_FILE", default="config.yaml")

config = EnvYAML(CONFIG_PATH)
API_PREFIX = config.get("api_prefix", "")
ROUTER_PREFIX = os.path.join(API_PREFIX, NAMESPACE) if API_PREFIX else ""

storage_client_factory = StorageClientFactory.from_config(config)
data_preprocessor = DataPreprocessor(config)
search_service_client = SearchServiceClient.from_config(config)

maintenance_tasks = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    maintenance_tasks.add(
        asyncio.create_task(task_cleaner(config["task_cleaner_interval"]))
    )
    maintenance_tasks.add(
        asyncio.create_task(
            reembedding_background_task(
                interval=config["reembed_interval"],
                search_service_client=search_service_client,
                config=config,
            )
        )
    )
    maintenance_tasks.add(
        asyncio.create_task(
            delta_load_background_task(
                interval=config["delta_load_interval"],
                bucket=storage_client_factory().bucket(config["bucket"]),
                data_preprocessor=data_preprocessor,
                search_service_client=search_service_client,
                prefix=config["bucket_prefix"],
            )
        )
    )
    maintenance_tasks.add(
        asyncio.create_task(
            delete_background_task(
                interval=config["delete_interval"],
                bucket=storage_client_factory().bucket(config["bucket"]),
                search_service_client=search_service_client,
                prefix=config["bucket_prefix"],
            )
        )
    )
    yield
    search_service_client.close()


router = APIRouter()


@router.get("/health-check")
def health_check():
    return {"status": "OK"}


@router.post("/events", response_model=OpenSearchResponse | str)
def ingest_item(
    storage: Annotated[storage.Client, Depends(storage_client_factory)],
    event: StorageChangeEvent,
    event_type: Annotated[str, Header(alias="eventType")],
    request: Request,
):
    try:
        if event_type == EVENT_TYPE_DELETE:
            try:
                return search_service_client.delete(event.blob_id)
            except HTTPStatusError as e:
                if e.response.status_code == 404:
                    msg = f"Delete event for {event.blob_id} is ignored, as the entry is not found in OSS"
                    logger.warning(msg)
                    return msg
                raise e
        else:
            return process_upsert_event(
                event=event,
                search_service_client=search_service_client,
                storage=storage,
                data_preprocessor=data_preprocessor,
            )
    except Exception as e:
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
        full_ingest,
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


# main app
app = FastAPI(title="Ingest Service", lifespan=lifespan)
app.include_router(router, prefix=ROUTER_PREFIX)
