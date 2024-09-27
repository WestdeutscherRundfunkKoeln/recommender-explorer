import os
from typing import Annotated, Any

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


@router.post("/documents/{document_id}")
def create_document(
    document_id: str,
    data: CreateDocumentRequest,
    oss_accessor: OssAccessor = Depends(get_oss_accessor),
):
    # Add data to index
    print(data, type(data))
    return oss_accessor.create_oss_doc(document_id, data)


@router.post("/documents")
def bulk_create_document(
    data: dict[str, CreateDocumentRequest],
    oss_accessor: OssAccessor = Depends(get_oss_accessor),
):
    # add data to index
    return oss_accessor.bulk_ingest(data)


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: str, oss_accessor: OssAccessor = Depends(get_oss_accessor)
):
    return oss_accessor.delete_oss_doc(document_id)


@router.get("/documents/{document_id}")
def get_document(
    document_id: str,
    fields: Annotated[str | None, Query()] = None,
    oss_accessor: OssAccessor = Depends(get_oss_accessor),
):
    _fields = fields.split(",") if fields else []
    return oss_accessor.get_oss_doc(document_id, _fields)


@router.post("/query")
def get_document_with_query(
    query: dict[str, Any],
    oss_accessor: OssAccessor = Depends(get_oss_accessor),
):
    return oss_accessor.get_oss_docs(query)


# TODO: search query for nearest neighbors

app = FastAPI(title="Search Service")
app.include_router(router, prefix=ROUTER_PREFIX)
