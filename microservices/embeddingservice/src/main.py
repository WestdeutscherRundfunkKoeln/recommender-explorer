import logging
from fastapi import FastAPI, APIRouter, HTTPException
from src.embed_text import EmbedText
from src.model_config_utils import (
    load_and_validate_model_config,
    get_model_names,
    get_full_model_config,
)
from src.constants import MODELS_KEY
from dto.embed_data import AddEmbeddingToDocRequest, EmbeddingRequest
from envyaml import EnvYAML
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

NAMESPACE = "embedding"

CONFIG_PATH = os.environ.get("CONFIG_FILE", default="config.yaml")

config = EnvYAML(CONFIG_PATH)
model_config_dict = load_and_validate_model_config(dict(config))
text_embedder = EmbedText(model_config_dict)

aggregated_model_name_config = get_model_names(model_config_dict)
aggregated_full_model_config = get_full_model_config(model_config_dict)

API_PREFIX = config.get("api_prefix", default="")
ROUTER_PREFIX = os.path.join(API_PREFIX, NAMESPACE) if API_PREFIX else ""
router = APIRouter()


@router.get("/health-check")
def health_check():
    # TODO: Add a more sensful check for service health! For instance check, if embedder is working now
    return {"status": "OK"}


@router.post("/embedding")
def get_embedding(data: EmbeddingRequest):
    return text_embedder.embed_text(data.embedText, data.models, data.returnEmbedText)


@router.post("/add-embedding-to-doc")
def add_embedding_to_document(data: AddEmbeddingToDocRequest):
    logger.info("Adding embedding to document %s", data.id)
    result = text_embedder.embed_text(data.embedText, data.models)
    text_embedder.add_embedding_to_document(data.id, result)
    ### Tobias - the result of the embedding operation is returned,
    ### but the success/failure of the search call is never tracked/caught
    return result


@router.get("/models")
def get_models():
    return aggregated_model_name_config


@router.get("/model_config/{key}")
def get_model_config(key: str):
    """
    Endpoint to return the model configuration based on a key provided as a path parameter.
    :param key: Key for which model configuration is requested (e.g., 'wdr' or 'br').
    :return: Model configuration if key exists, else an error.
    """
    if key in config[MODELS_KEY]:
        return config[MODELS_KEY][key]
    raise HTTPException(status_code=404, detail=f"Model configuration not found for key: {key}")


@router.get("/model_config")
def get_all_model_configs():
    """
    Endpoint to return aggregated 'c2c_models' and 'u2c_models' from all configurations.
    If either 'c2c_models' or 'u2c_models' is missing, it is ignored in the output.
    Only the first occurrence of each model key is included for each model type.

    :return: Aggregated 'c2c_models' and 'u2c_models' configurations.
    """
    return aggregated_full_model_config


# main app
app = FastAPI(title="Embedding Service")

app.include_router(router, prefix=ROUTER_PREFIX)