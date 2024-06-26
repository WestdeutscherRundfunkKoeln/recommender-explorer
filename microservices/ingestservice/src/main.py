import json
import logging
import os
from typing import Annotated

import httpx
from envyaml import EnvYAML
from fastapi import Depends, FastAPI, APIRouter, Header
from fastapi.exceptions import HTTPException
from google.api_core.exceptions import GoogleAPICallError
from google.cloud import storage
from google.oauth2 import service_account
from pydantic import ValidationError
from src.models import FullLoadRequest, OpenSearchResponse, StorageChangeEvent
from src.preprocess_data import DataPreprocessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


NAMESPACE = "ingest"
EVENT_TYPE_DELETE = "OBJECT_DELETE"

CONFIG_PATH = os.environ.get("CONFIG_FILE", default="config.yaml")
BASE_URL_SEARCH = os.environ.get("BASE_URL_SEARCH", default="")
API_PREFIX = os.environ.get("API_PREFIX", default="")
ROUTER_PREFIX = os.path.join(API_PREFIX, NAMESPACE) if API_PREFIX else ""
STORAGE_SERVICE_ACCOUNT = os.environ.get("STORAGE_SERVICE_ACCOUNT", default="")

config = EnvYAML(CONFIG_PATH)
data_preprocessor = DataPreprocessor(config)


def request(data, url):
    # TODO: Remove timeout when search service is implemented
    return httpx.post(
        url, json=data, timeout=None, headers={"x-api-key": config["api_key"]}
    ).json()


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
        return httpx.delete(
            f"{BASE_URL_SEARCH}/delete-data",
            params={"document_id": id},
            headers={"x-api-key": config["api_key"]}
        ).json()

    try:
        document = data_preprocessor.map_data(download_document(storage, event))
        document_json = document.model_dump()
        # Add metadata to index
        retval = request(document_json, f"{BASE_URL_SEARCH}/create-single-document")
        # Trigger embedding service to add embeddings to index
        data_preprocessor.add_embeddings(document)
        return retval  # TODO: check for meaningful return object. kept for backward compatibility?
    except ValidationError as exc:
        error_message = repr(exc.errors()[0]["type"])
        logger.error("Validation error: " + repr(exc.errors()))
        raise HTTPException(status_code=422, detail=error_message)


@router.post("/ingest-multiple-items")
def bulk_ingest(
    body: FullLoadRequest,
    storage: Annotated[storage.Client, Depends(get_storage_client)],
):
    bucket = storage.bucket(body.bucket)
    item_dict = {}
    for blob in bucket.list_blobs(match_glob=f"{body.prefix}*.json"):
        logger.info(f"Downloading {blob.name}")
        data = json.loads(blob.download_as_text())
        try:
            mapped_data = data_preprocessor.map_data(data)
            # Trigger embedding service to add embeddings to index
            data_preprocessor.add_embeddings(mapped_data)
        except ValidationError:
            logger.error(
                "Error during preprocessing of file %s", blob.name, exc_info=True
            )
            continue
        item_dict[mapped_data.id] = mapped_data.model_dump()
    return request(item_dict, f"{BASE_URL_SEARCH}/create-multiple-documents")


app = FastAPI(title="Ingest Service")
app.include_router(router, prefix=ROUTER_PREFIX)
