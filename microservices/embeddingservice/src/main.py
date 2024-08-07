from fastapi import FastAPI, APIRouter
from src.embed_text import EmbedText
from dto.embed_data import AddEmbeddingToDocRequest, EmbeddingRequest
from envyaml import EnvYAML
import os

NAMESPACE = "embedding"

CONFIG_PATH = os.environ.get("CONFIG_FILE", default="config.yaml")

# TODO: Remove direct environment var access, use config file instead!!
API_PREFIX = os.environ.get("API_PREFIX", default="")
ROUTER_PREFIX = os.path.join(API_PREFIX, NAMESPACE) if API_PREFIX else ""

config = EnvYAML(CONFIG_PATH)
text_embedder = EmbedText(config)

router = APIRouter()


@router.get("/health-check")
def health_check():
    # TODO: Add a more sensful check for service health!
    # For instance check, if embedder is working
    return {"status": "OK"}


@router.post("/embedding")
def get_embedding(data: EmbeddingRequest):
    return text_embedder.embed_text(data.embedText, data.models)


@router.post("/add-embedding-to-doc")
def add_embedding_to_document(data: AddEmbeddingToDocRequest):
    result = text_embedder.embed_text(data.embedText, [])
    text_embedder.add_embedding_to_document(data.id, result)
    return result


app = FastAPI(title="Embedding Service")
app.include_router(router, prefix=ROUTER_PREFIX)
