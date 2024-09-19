from typing import Any
from fastapi import HTTPException
import httpx


class SearchServiceClient:
    def __init__(self, client: httpx.Client):
        self.client = client

    @classmethod
    def from_config(cls, config) -> "SearchServiceClient":
        base_url = config["base_url_search"]
        api_key = config["api_key"]
        client = httpx.Client(base_url=base_url, headers={"x-api-key": api_key})
        return cls(client)

    def close(self):
        self.client.close()

    def delete(self, id: str):
        response = self.client.delete(
            f"/documents/{id}",
        )
        _raise_for_status(response)
        return response.json()

    def create_single_document(self, id: str, document: dict):
        response = self.client.post(f"/documents/{id}", json=document)
        _raise_for_status(response)
        return response.json()

    def create_multiple_documents(self, documents: dict[str, Any]):
        response = self.client.post("/documents", json=documents)
        _raise_for_status(response)
        return response

    def get(self, id: str, fields: list[str] | None = None):
        response = self.client.get(
            f"/documents/{id}",
            params={"fields": ",".join(fields) if fields else None},
        )
        _raise_for_status(response)
        return response.json()["hits"]["hits"][0]["_source"]

    def query(self, query: dict):
        response = self.client.post("/query", json=query)
        _raise_for_status(response)
        return response.json()


def _raise_for_status(response: httpx.Response):
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
