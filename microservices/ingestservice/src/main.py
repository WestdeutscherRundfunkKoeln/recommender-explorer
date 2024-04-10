import json
import logging
import os
from glob import glob
from typing import Annotated

import httpx
from envyaml import EnvYAML
from fastapi import Depends, FastAPI, APIRouter
from fastapi.exceptions import HTTPException
from google.api_core.exceptions import GoogleAPICallError
from google.cloud import storage
from google.oauth2 import service_account
from src.models import OpenSearchResponse, StorageChangeEvent
from src.preprocess_data import DataPreprocessor

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


NAMESPACE = "ingest"

CONFIG_PATH = os.environ.get("CONFIG_FILE", default="config.yaml")
BASE_URL_SEARCH = os.environ.get("BASE_URL_SEARCH", default="")
API_PREFIX = os.environ.get("API_PREFIX", default="")
ROUTER_PREFIX = os.path.join(API_PREFIX, NAMESPACE) if API_PREFIX else ""
STORAGE_SERVICE_ACCOUNT = os.environ.get("STORAGE_SERVICE_ACCOUNT", default="")

config = EnvYAML(CONFIG_PATH)
data_preprocessor = DataPreprocessor(config)


def request(data, url):
    response = httpx.post(
        url, json=data, timeout=None
    )  # TODO: remove timeout when search service is implemented
    return response.json()


def get_storage_client():
    bucket_service_account = json.loads(STORAGE_SERVICE_ACCOUNT)
    credentials = service_account.Credentials.from_service_account_info(
        bucket_service_account
    )
    storage_client = storage.Client(credentials=credentials)
    return storage_client


def download_document(
    event: StorageChangeEvent,
    storage: Annotated[storage.Client, Depends(get_storage_client)],
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


@router.post("/ingest-single-item", response_model=OpenSearchResponse)
def ingest_item(raw_document: Annotated[dict, Depends(download_document)]):
    mapped_data = data_preprocessor.preprocess_data(raw_document)
    data_preprocessor.add_embeddings(mapped_data)
    # add data to index
    return request(
        mapped_data.model_dump(), f"{BASE_URL_SEARCH}/create-single-document"
    )


@router.post("/delete-single-item", response_model=OpenSearchResponse)
def delete_item(raw_document: Annotated[dict, Depends(download_document)]):
    document = data_preprocessor.preprocess_data(raw_document)
    return httpx.delete(f"{BASE_URL_SEARCH}/{document.id}")


@router.post("/ingest-multiple-items")
def bulk_ingest(bucket):
    item_dict = {}
    for fname in glob(bucket + "*.json"):
        with open(fname, "r") as f:
            data = json.load(f)
            mapped_data = data_preprocessor.preprocess_data(data)
            item_dict[mapped_data.id] = mapped_data.model_dump()
    search_response = request(item_dict, f"{BASE_URL_SEARCH}/create-multiple-documents")

    return search_response


app = FastAPI(title="Ingest Service")
app.include_router(router, prefix=ROUTER_PREFIX)