#main.py

# Start with
# FULL_PATH='<your path to config file>' uvicorn src.main:app --reload

from fastapi import FastAPI
from dto.recoexplorer_item import RecoExplorerItem
from src.map_data import DataMapper
from src.oss_accessor import OssAccessor
from dto.media_data import MediaData
from dto.sophora_data import SophoraData
from envyaml import EnvYAML
import os

app = FastAPI(title="Ingest Service")

@app.post("/map-data", response_model=RecoExplorerItem)
def map_data(config, data: SophoraData) -> RecoExplorerItem: # input = entity
    data_mapper = DataMapper()
    mapped_data = data_mapper.map_data(config, data)
    return mapped_data

@app.post("/ingest-data") #, response_model=RecoExplorerItem)
def ingest_data(client, data: SophoraData): # CHANGE SOPHORADATA TO JSON, CHECK IN REST OF CODE
    # get values from config
    full_path = os.environ.get("FULL_PATH")
    config = EnvYAML(full_path)

    # map data
    mapped_data = map_data(config, data).model_dump()

    # add data to index
    oss_doc_generator = OssAccessor()
    response = oss_doc_generator.create_oss_doc(config, mapped_data)

    return response
