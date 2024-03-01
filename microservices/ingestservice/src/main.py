#main.py

# Start with
# FULL_PATH='<your path to config file>' uvicorn src.main:app --reload

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from dto.recoexplorer_item import RecoExplorerItem
from src.map_data import DataMapper
from src.oss_accessor import OssAccessor
from envyaml import EnvYAML
import os

app = FastAPI(title="Ingest Service")
# get values from config
full_path = os.environ.get("CONFIG_FILE", default='config.yaml')
config = EnvYAML(full_path)
data_mapper = DataMapper(config)
oss_doc_generator = OssAccessor(config)


@app.post("/ingest-data")
def ingest_data(data: dict):
    # map data
    try:
        mapped_data = data_mapper.map_data(data).model_dump()
    except ValidationError as exc:
        error_message=repr(exc.errors()[0]['type'])
        raise HTTPException(status_code=422, detail=error_message)

    # add data to index
    response = oss_doc_generator.create_oss_doc(mapped_data)

    return response

@app.delete("/delete-data/{id}")
def delete_data(id):
    # Get ID from path parameter
    # Then change function in oss_accessor to delete item from OS index
    pass