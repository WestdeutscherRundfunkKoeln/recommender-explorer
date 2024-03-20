from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from src.map_data import DataMapper
from envyaml import EnvYAML
import os
import httpx

app = FastAPI(title="Ingest Service")
# get values from config
full_path = os.environ.get("CONFIG_FILE", default='config.yaml')
config = EnvYAML(full_path)
data_mapper = DataMapper(config)

URL_EMBEDDING = os.environ.get("URL_EMBEDDING")
URL_SEARCH = os.environ.get("URL_SEARCH")

def request(data, url):
    response = httpx.post(url, json=data, timeout = None) # TODO: remove timeout when search service is implemented
    return response.json()

@app.get("/health-check")
def health_check():
    return {"status": "OK"}

@app.post("/ingest-data")
def ingest_data(data: dict):
    # map data
    try:
        mapped_data = data_mapper.map_data(data).model_dump() # TODO: Find out what causes triple quotation marks in long description and fix it
    except ValidationError as exc:
        error_message=repr(exc.errors()[0]['type'])
        raise HTTPException(status_code=422, detail=error_message)
    request_payload = {"id": mapped_data["id"],
                       "embedText": mapped_data["embedText"]}
    embedding_response = request(request_payload, URL_EMBEDDING)

    mapped_data["embedding"] = embedding_response["embedding"]
    mapped_data["embedTextHash"] = embedding_response["hash"]

    # add data to index
    search_response = request(mapped_data, URL_SEARCH) # TODO: Only works if recoexplorer_item has availableFrom and availableTo as string instead of datetime

    return search_response
