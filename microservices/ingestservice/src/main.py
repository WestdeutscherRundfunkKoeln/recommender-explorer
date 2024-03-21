from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from src.preprocess_data import DataPreprocessor
from envyaml import EnvYAML
import os
import httpx
from glob import glob
import json

app = FastAPI(title="Ingest Service")
# get values from config
full_path = os.environ.get("CONFIG_FILE", default='config.yaml')
config = EnvYAML(full_path)
data_preprocessor = DataPreprocessor(config)

URL_SEARCH_SINGLE = os.environ.get("URL_SEARCH_SINGLE")
URL_SEARCH_BULK = os.environ.get("URL_SEARCH_BULK")

def request(data, url):
    response = httpx.post(url, json=data, timeout = None) # TODO: remove timeout when search service is implemented
    return response.json()


@app.post("/ingest-single-item")
def ingest_item(data: dict):
    mapped_data = data_preprocessor.preprocess_data(data)
    # add data to index
    search_response = request(mapped_data, URL_SEARCH_SINGLE)

    return search_response


@app.post("/ingest-multiple-items")
def bulk_ingest(bucket):
    item_dict = {}
    for fname in glob(bucket+"*.json"):
        with open(fname, 'r') as f:
            data = json.load(f)
            mapped_data = data_preprocessor.preprocess_data(data)
            item_dict[mapped_data['id']] = mapped_data
    search_response = request(item_dict, URL_SEARCH_BULK)

    return search_response

