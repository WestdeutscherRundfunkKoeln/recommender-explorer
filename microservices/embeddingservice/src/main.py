from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from src.embed_text import EmbedText
from dto.embed_data import EmbedData
from envyaml import EnvYAML
import os

app = FastAPI(title="Embedding Service")
# get values from config
full_path = os.environ.get("CONFIG_FILE", default='config.yaml')
config = EnvYAML(full_path)
text_embedder = EmbedText(config)

@app.post("/get-embedding")
def get_embedding(data: dict):
    text_to_embed = data['embedText']
    try:
        result = text_embedder.embed_text(text_to_embed)
    except ValidationError as exc:
        error_message = repr(exc.errors()[0]['type'])
        raise HTTPException(status_code=422, detail=error_message)  # TODO: return here

    return result

@app.post("/add-embedding-to-doc")
def add_embedding_to_document(data: EmbedData):
    id = data.id
    text_to_embed = data.embedText

    try:
        result = text_embedder.embed_text(text_to_embed)
        text_embedder.add_embedding_to_document(id, result)
    except ValidationError as exc:
        error_message = repr(exc.errors()[0]['type'])
        raise HTTPException(status_code=422, detail=error_message)  # TODO: return here

    return result