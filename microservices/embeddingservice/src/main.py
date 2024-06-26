from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import ValidationError
from src.embed_text import EmbedText
from dto.embed_data import EmbedData
from envyaml import EnvYAML
import os

NAMESPACE = "embedding"

CONFIG_PATH = os.environ.get("CONFIG_FILE", default="config.yaml")

#TODO: Remove direct environment var access, use config file instead!!
API_PREFIX = os.environ.get("API_PREFIX", default="")
ROUTER_PREFIX = os.path.join(API_PREFIX, NAMESPACE) if API_PREFIX else ""

config = EnvYAML(CONFIG_PATH)
text_embedder = EmbedText(config)

router = APIRouter()


@router.get("/health-check")
def health_check():
    #TODO: Add a more sensful check for service health!
    # For instance check, if embedder is working
    return {"status": "OK"}

@router.post("/embedding")
def get_embedding(data: EmbedData):
    text_to_embed = data.embedText
    models_to_use = data.models
    try:
        result = text_embedder.embed_text(text_to_embed, models_to_use)
    except ValidationError as exc:
        error_message = repr(exc.errors()[0]['type'])
        raise HTTPException(status_code=422, detail=error_message)

    return result

@router.post("/add-embedding-to-doc")
def add_embedding_to_document(data: EmbedData):
    id = data.id
    text_to_embed = data.embedText

    try:
        result = text_embedder.embed_text(text_to_embed, [])
        text_embedder.add_embedding_to_document(id, result)
    except ValidationError as exc:
        error_message = repr(exc.errors()[0]["type"])
        raise HTTPException(status_code=422, detail=error_message)  # TODO: Return here

    return result


app = FastAPI(title="Embedding Service")
app.include_router(router, prefix=ROUTER_PREFIX)

