from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from src.map_data import DataMapper
from src.oss_accessor import OssAccessor
from envyaml import EnvYAML
import os
import httpx

app = FastAPI(title="Ingest Service")
# get values from config
full_path = os.environ.get("CONFIG_FILE", default='config.yaml')
config = EnvYAML(full_path)
data_mapper = DataMapper(config)
oss_doc_generator = OssAccessor(config)

URL = "http://localhost:8001/embedding" # TODO: from config as env variable, one for host, one for path


def request(data):
    response = httpx.post(URL, json=data, timeout = None) # TODO: find alternative to timeout=None
    return response.json()


@app.post("/ingest-data")
def ingest_data(data: dict):
    # map data
    try:
        mapped_data = data_mapper.map_data(data).model_dump()
    except ValidationError as exc:
        error_message=repr(exc.errors()[0]['type'])
        raise HTTPException(status_code=422, detail=error_message) # TODO: get correct error message

    request_payload = {"id": mapped_data['id'],
                       "embedText": mapped_data['embedText']}
    embedding_response= request(request_payload)

    mapped_data['embedding'] = embedding_response['embedding']
    mapped_data['embedTextHash'] = embedding_response['hash']

    # add data to index
    response = oss_doc_generator.create_oss_doc(mapped_data)

    return response

@app.delete("/delete-data/{id}")
def delete_data(id):
    response = oss_doc_generator.delete_oss_doc(id)
    return response
