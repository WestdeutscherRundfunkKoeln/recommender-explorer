import os

from envyaml import EnvYAML
from fastapi import APIRouter, FastAPI

from src.oss_accessor import OssAccessor

NAMESPACE = "search"

CONFIG_PATH = os.environ.get("CONFIG_FILE", default="config.yaml")
API_PREFIX = os.environ.get("API_PREFIX", default="")
ROUTER_PREFIX = os.path.join(API_PREFIX, NAMESPACE) if API_PREFIX else ""

config = EnvYAML(CONFIG_PATH)
oss_doc_generator = OssAccessor(config)

router = APIRouter()


@router.get("/health-check")
def health_check():
    return {"status": "OK"}


@router.post("/create-single-document")
def create_document(data: dict):
    print("---------------")
    print(data)
    print("---------------")
    # Add data to index
    response = oss_doc_generator.create_oss_doc(data)
    return response


@router.post("/create-multiple-documents")
def bulk_create_document(data: dict):
    # add data to index
    response = oss_doc_generator.bulk_ingest(data)
    return response


@router.delete("/delete-data")
def delete_document(document_id: str):
    response = oss_doc_generator.delete_oss_doc(document_id)
    return response


# TODO: search query for nearest neighbors

app = FastAPI(title="Search Service")
app.include_router(router, prefix=ROUTER_PREFIX)
