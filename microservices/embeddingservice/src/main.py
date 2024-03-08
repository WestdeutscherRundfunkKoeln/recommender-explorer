from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import ValidationError
from src.embed_text import EmbedText
from dto.embed_data import EmbedData
from envyaml import EnvYAML
import os

NAMESPACE = "embedding"

CONFIG_PATH = os.environ.get("CONFIG_FILE", default="config.yaml")
API_PREFIX = os.environ.get("API_PREFIX", default="")
ROUTER_PREFIX = os.path.join(API_PREFIX, NAMESPACE) if API_PREFIX else ""

config = EnvYAML(CONFIG_PATH)
text_embedder = EmbedText(config)

router = APIRouter()


@router.get("/health-check")
def health_check():
    return {"status": "OK"}


@router.post("/embedding")
def embedding(data: EmbedData):
    id = data.id
    text_to_embed = data.embedText

    try:
        result = text_embedder.embed_text(id, text_to_embed)
    except ValidationError as exc:
        error_message = repr(exc.errors()[0]["type"])
        raise HTTPException(status_code=422, detail=error_message)  # TODO: return here

    return result


app = FastAPI(title="Embedding Service")
app.include_router(router, prefix=ROUTER_PREFIX)
