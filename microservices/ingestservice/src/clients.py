from typing import Any
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
        response.raise_for_status()
        return response.json()

    def create_single_document(self, id: str, document: dict):
        response = self.client.post(
            f"/documents/{id}",
            json=document,
        )
        response.raise_for_status()
        return response.json()

    def create_multiple_documents(self, documents: dict[str, Any]):
        response = self.client.post("/documents", json=documents)
        response.raise_for_status()
        return response

    def get(self, id: str, fields: list[str] | None = None):
        response = self.client.get(
            f"/documents/{id}",
            params={"fields": ",".join(fields) if fields else None},
        )
        response.raise_for_status()
        return response.json()["_source"]

    def query(self, query: dict):
        response = self.client.post("/query", json=query)
        response.raise_for_status()
        return response.json()

    def scan(self, query: dict):
        response = self.client.post("/scan", json=query)
        response.raise_for_status()
        return response.json()
