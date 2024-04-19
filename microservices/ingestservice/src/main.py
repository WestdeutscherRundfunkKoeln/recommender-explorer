from fastapi import FastAPI, APIRouter
from src.preprocess_data import DataPreprocessor
from envyaml import EnvYAML
import os
import httpx
from glob import glob
import json

NAMESPACE = "ingest"

CONFIG_PATH = os.environ.get("CONFIG_FILE", default="config.yaml")
BASE_URL_SEARCH = os.environ.get("BASE_URL_SEARCH", default="")
API_PREFIX = os.environ.get("API_PREFIX", default="")
ROUTER_PREFIX = os.path.join(API_PREFIX, NAMESPACE) if API_PREFIX else ""

config = EnvYAML(CONFIG_PATH)
data_preprocessor = DataPreprocessor(config)


def request(data, url):
    # TODO: remove timeout when search service is implemented
    response = httpx.post(url, json=data, timeout = None)
    return response.json()


router = APIRouter()


@router.get("/health-check")
def health_check():
    return {"status": "OK"}


@router.post("/ingest-single-item")
def ingest_item(data: dict):
    mapped_data = data_preprocessor.preprocess_data(data)
    # add data to index
    search_response = request(mapped_data,f"{BASE_URL_SEARCH}/create-single-document")

    return search_response


@router.post("/ingest-multiple-items")
def bulk_ingest(bucket):
    item_dict = {}
    for fname in glob(bucket+"*.json"):
        with open(fname, 'r') as f:
            data = json.load(f)
            mapped_data = data_preprocessor.preprocess_data(data)
            item_dict[mapped_data['id']] = mapped_data
    search_response = request(item_dict, f"{BASE_URL_SEARCH}/create-multiple-documents")

    return search_response


@router.delete("/delete-data/{id}")
def delete_document(document_id):
    # TODO @Jessica
    return {"delete": "NOK"}


app = FastAPI(title="Ingest Service")
app.include_router(router, prefix=ROUTER_PREFIX)
