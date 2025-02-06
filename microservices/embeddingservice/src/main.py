import json
import logging
from fastapi import FastAPI, APIRouter, HTTPException
from src.embed_text import EmbedText
from dto.embed_data import AddEmbeddingToDocRequest, EmbeddingRequest
from envyaml import EnvYAML
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

NAMESPACE = "embedding"

CONFIG_PATH = os.environ.get("CONFIG_FILE", default="config.yaml")

config = EnvYAML(CONFIG_PATH)
config_dict = dict(config)

if isinstance(config_dict["models"], str):
    try:
        config_dict["models"] = json.loads(config_dict["models"])
    except json.JSONDecodeError as e:
        logger.error("Error parsing models config: %s", e)
        raise e

text_embedder = EmbedText(config_dict)

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
    ### Tobias - the result of the embedding operation is returned,
    ### but the success/failure of the search call is never tracked/caught
    return result


@router.get("/models")
def get_models():
    return [
        model_config["model_name"]
        for model, model_config in config["models"]["c2c_models"].items()
    ]


@router.get("/model_config/{key}")
def get_model_config(key: str):
    """
    Endpoint to return the model configuration based on a key provided as a path parameter.
    :param key: Key for which model configuration is requested (e.g., 'wdr' or 'br').
    :return: Model configuration if key exists, else an error.
    """
    if key in config["models"]:
        return config["models"][key]
    raise HTTPException(status_code=404, detail=f"Model configuration not found for key: {key}")


@router.get("/model_config")
def get_all_model_configs():
    """
    Endpoint to return aggregated 'c2c_models' and 'u2c_models' from all configurations.
    If either 'c2c_models' or 'u2c_models' is missing, it is ignored in the output.
    Only the first occurrence of each model key is included for each model type.

    :return: Aggregated 'c2c_models' and 'u2c_models' configurations.
    """
    aggregated_c2c_models = {}
    aggregated_u2c_models = {}

    for key, value in config["models"].items():
        if "c2c_models" in value:
            for model_key, model_config in value["c2c_models"].items():
                if model_key not in aggregated_c2c_models:
                    aggregated_c2c_models[model_key] = model_config
        if "u2c_models" in value:
            for model_key, model_config in value["u2c_models"].items():
                if model_key not in aggregated_u2c_models:
                    aggregated_u2c_models[model_key] = model_config
    response = {}
    if aggregated_c2c_models:
        response["c2c_models"] = aggregated_c2c_models
    if aggregated_u2c_models:
        response["u2c_models"] = aggregated_u2c_models

    return response


# main app
app = FastAPI(title="Embedding Service")

app.include_router(router, prefix=ROUTER_PREFIX)