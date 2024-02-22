#main.py

# Start with uvicorn main:app --reload

from fastapi import FastAPI
from microservices.ingestservice.config import settings
from microservices.ingestservice.dto.recoexplorer_item import RecoExplorerItem
from microservices.ingestservice.data_mapper import DataMapper
from microservices.ingestservice.dto.media_data import MediaData
from microservices.ingestservice.dto.sophora_data import SophoraData
import os
import logging
from opensearchpy import OpenSearch, RequestsHttpConnection, helpers
from envyaml import EnvYAML
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

app = FastAPI(title=settings.PROJECT_NAME,version=settings.PROJECT_VERSION)

path = 'microservices/ingestservice/' # THIS NEEDS TO BE CHANGED

@app.post("/map-data", response_model=RecoExplorerItem)
def map_data(data: MediaData) -> RecoExplorerItem: # input = entity
    data_mapper = DataMapper()
    mapped_data = data_mapper.map_data(data)
    return mapped_data

@app.post("/ingest-data") #, response_model=RecoExplorerItem)
def ingest_data(client, data: SophoraData) -> RecoExplorerItem: # CHANGE SOPHORADATA TO JSON, CHECK IN REST OF CODE
    mapped_data = map_data(data).model_dump()


    # get values from config
    config_full_path = path + '/config_' + client + '.yaml' # PER RUNTIME PARAMETER -> CHECK FASTAPI DOCUMENTATION
    config = EnvYAML(config_full_path)

    # MOVE THIS TO SEPERATE FILE + pass config
    target_idx_name = config['opensearch']['index']

    host = config['opensearch']['host']
    auth = (config['opensearch']['user'],
            config['opensearch']['pass'])
    port = config['opensearch']['port']

    logger.info('Host: ' + host)


    # initialize OSS client
    oss_client = OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=600,
    )

    # add document to index
    response = oss_client.index(
        index=target_idx_name,
        body=mapped_data,
        id=f"{mapped_data['id']}",
        refresh=True
    )

    # logger.info('Response: ' + response)

    return mapped_data # RETURN STATUS CODE OR REPORT