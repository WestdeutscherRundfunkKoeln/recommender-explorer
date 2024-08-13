import os
from typing import Annotated

from envyaml import EnvYAML
from fastapi import APIRouter, FastAPI, Depends, Query
from src.oss_accessor import OssAccessor
from src.models import CreateDocumentRequest

NAMESPACE = "search"

CONFIG_PATH = os.environ.get("CONFIG_FILE", default="config.yaml")
API_PREFIX = os.environ.get("API_PREFIX", default="")
ROUTER_PREFIX = os.path.join(API_PREFIX, NAMESPACE) if API_PREFIX else ""

config = EnvYAML(CONFIG_PATH)
oss_doc_generator = OssAccessor.from_config(config)

router = APIRouter()


def get_oss_accessor():
    return oss_doc_generator


@router.get("/health-check")
def health_check():
    return {"status": "OK"}


@router.post("/create-single-document")
def create_document(
    data: CreateDocumentRequest, oss_accessor: OssAccessor = Depends(get_oss_accessor)
):
    # Add data to index
    print(data, type(data))
    response = oss_accessor.create_oss_doc(data)
    return response


@router.post("/create-multiple-documents")
def bulk_create_document(
    data: dict[str, CreateDocumentRequest],
    oss_accessor: OssAccessor = Depends(get_oss_accessor),
):
    # add data to index
    response = oss_accessor.bulk_ingest(data)
    return response


@router.delete("/delete-data")
def delete_document(
    document_id: str, oss_accessor: OssAccessor = Depends(get_oss_accessor)
):
    response = oss_accessor.delete_oss_doc(document_id)
    return response


@router.get("/document/{document_id}")
def get_document(
    document_id: str,
    fields: Annotated[str | None, Query()] = None,
    oss_accessor: OssAccessor = Depends(get_oss_accessor),
):
    _fields = fields.split(",") if fields else []
    response = oss_accessor.get_oss_doc(document_id, _fields)
    return response


# TODO: search query for nearest neighbors

app = FastAPI(title="Search Service")
app.include_router(router, prefix=ROUTER_PREFIX)
