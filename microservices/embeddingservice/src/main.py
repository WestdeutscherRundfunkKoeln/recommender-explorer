import logging
from fastapi import FastAPI, APIRouter
from src.embed_text import EmbedText
from dto.embed_data import AddEmbeddingToDocRequest, EmbeddingRequest
from envyaml import EnvYAML
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

NAMESPACE = "embedding"

CONFIG_PATH = os.environ.get("CONFIG_FILE", default="config.yaml")

config = EnvYAML(CONFIG_PATH)
text_embedder = EmbedText(config)

API_PREFIX = config.get("api_prefix", default="")
ROUTER_PREFIX = os.path.join(API_PREFIX, NAMESPACE) if API_PREFIX else ""
router = APIRouter()


@router.get("/health-check")
def health_check():
    # TODO: Add a more sensful check for service health! For instance check, if embedder is working now
    return {"status": "OK"}


@router.post("/embedding")
def get_embedding(data: EmbeddingRequest):
    return text_embedder.embed_text(data.embedText, data.models)


@router.post("/add-embedding-to-doc")
def add_embedding_to_document(data: AddEmbeddingToDocRequest):
    logger.info("Adding embedding to document %s", data.id)
    result = text_embedder.embed_text(data.embedText, data.models)
    text_embedder.add_embedding_to_document(data.id, result)
    return result


@router.get("/models")
def get_models():
    return list(text_embedder.models.keys())


app = FastAPI(title="Embedding Service")

app.include_router(router, prefix=ROUTER_PREFIX)
