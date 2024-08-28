import asyncio
import logging
from typing import Any

import httpx
from envyaml import EnvYAML
from src.clients import SearchServiceClient

logger = logging.getLogger(__name__)


async def reembedding_background_task(
    interval_seconds: float, search_service_client: SearchServiceClient, config: EnvYAML
):
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await embed_partially_created_records(search_service_client, config)
        except Exception:
            logger.error("Error during re-embedding task", exc_info=True)


async def embed_partially_created_records(
    search_service_client: SearchServiceClient, config: EnvYAML
):
    async with httpx.AsyncClient(
        base_url=config["base_url_embedding"], headers={"x-api-key": config["api_key"]}
    ) as embedding_service_client:
        models = await get_models_info(embedding_service_client)

        records = await get_partially_created_records(search_service_client, models)

        for record in records:
            await embed_partially_created_record(
                embedding_service_client, models, record
            )


async def embed_partially_created_record(
    client: httpx.AsyncClient, models: list[str], record: dict[str, Any]
):
    models_for_embedding = [
        model for model in models if (model not in record) or (not record[model])
    ]

    await client.post(
        "/add-embedding-to-doc",
        json={
            "id": record["id"],
            "embedText": record["embedText"],
            "models": models_for_embedding,
        },
    )


async def get_models_info(client: httpx.AsyncClient) -> list[str]:
    response = await client.get("/models")
    response.raise_for_status()

    models = response.json()
    if not models:
        raise Exception("No models found in embedding service.")

    return models


async def get_partially_created_records(
    search_service_client: SearchServiceClient, models: list[str]
) -> list[dict[str, Any]]:
    response = await asyncio.to_thread(search_service_client.query, build_query(models))

    hits = response.get("hits", {}).get("hits", [])
    if not hits:
        raise Exception("No partially created records found.")

    return [hit["_source"] for hit in hits]


def build_query(models: list[str]) -> dict:
    query = {
        "_source": {"includes": ["id", "embedText", *models]},
        "query": {
            "bool": {
                "should": [
                    {"bool": {"must_not": [{"exists": {"field": model}}]}}
                    for model in models
                ]
            }
        },
    }
    logger.debug("Maintenance query: %s", query)
    return query