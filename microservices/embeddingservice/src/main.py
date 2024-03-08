from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from src.embed_text import EmbedText
from envyaml import EnvYAML
import os

app = FastAPI(title="Embedding Service")
# get values from config
full_path = os.environ.get("CONFIG_FILE", default='config.yaml')
config = EnvYAML(full_path)
text_embedder = EmbedText(config)

@app.post("/embedding")
def embedding(data: dict): # TODO: not dict but dto embed_text
    id = data['id']
    text_to_embed = data['embedText']
    result = text_embedder.embed_text(id, text_to_embed)

    return result

#######################################################################
@app.post("/ingest-embedding")
def ingest_data(data: dict):
    # map data
    try:
        mapped_data = data_mapper.map_data(data).model_dump()
    except ValidationError as exc:
        error_message=repr(exc.errors()[0]['type'])
        raise HTTPException(status_code=422, detail=error_message) # TODO: get correct error message

    # add data to index
    response = oss_doc_generator.create_oss_doc(mapped_data)

    return response
#######################################################################
