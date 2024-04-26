from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from src.oss_accessor import OssAccessor
from envyaml import EnvYAML
import os

app = FastAPI(title="Search Service")
# get values from config
full_path = os.environ.get("CONFIG_FILE", default='config.yaml')
config = EnvYAML(full_path)
oss_doc_generator = OssAccessor(config)


@app.post("/create-single-document")
def create_document(data: dict):
    # add data to index
    response = oss_doc_generator.create_oss_doc(data)
    return response

@app.delete("/delete-data/{id}")
def delete_document(document_id):
    response = oss_doc_generator.delete_oss_doc(document_id)
    return response

@app.post("/create-multiple-documents")
def bulk_create_document(data: dict):
    # add data to index
    response = oss_doc_generator.bulk_ingest(data)
    return response

# TODO: search query for nearest neighbors