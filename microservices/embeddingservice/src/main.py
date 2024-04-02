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

@app.post("/embedding")
def embedding(data: EmbedData):
    id = data.id
    text_to_embed = data.embedText

    try:
        result = text_embedder.embed_text(id, text_to_embed)
    except ValidationError as exc:
        error_message = repr(exc.errors()[0]['type'])
        raise HTTPException(status_code=422, detail=error_message)  # TODO: return here

    return result
