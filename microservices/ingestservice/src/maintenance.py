import asyncio
import aiocron
import datetime
import logging
from typing import Any

import httpx
from envyaml import EnvYAML
from google.cloud import storage
from src.clients import SearchServiceClient
from src.ingest import delete_batch, delta_ingest
from src.preprocess_data import DataPreprocessor
from src.task_status import TaskStatus

logger = logging.getLogger(__name__)


async def reembedding_background_task(
    interval: str, search_service_client: SearchServiceClient, config: EnvYAML
):
    while True:
        await aiocron.crontab(interval).next()
        logger.info("Running re-embedding task")
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

        responses = []
        for record in records:
            response = await embed_partially_created_record(
                embedding_service_client, models, record
            )
            responses.append(response)

        for response in responses:
            if response.status_code != 200:
                logger.error(
                    "Error during re-embedding task. Response: %s", response.text
                )
        logger.info("Re-embedding task is done")


async def embed_partially_created_record(
    client: httpx.AsyncClient, models: list[str], record_kv: tuple[str, dict[str, Any]]
):
    id, record = record_kv
    models_for_embedding = [
        model for model in models if (model not in record) or (not record[model])
    ]

    try:
        logger.info(
            "Calling embedding service to re-embed doc with id [" + str(id) + "]"
        )
        result = await client.post(
            "/add-embedding-to-doc",
            timeout=180,
            json={
                "id": id,
                "embedText": record["embedText"],
                "models": models_for_embedding,
            },
        )
        return result
    except httpx.ReadTimeout:
        logger.debug("Re-Embed Call of item [" + str(id) + "] timed out")
        pass


async def get_models_info(client: httpx.AsyncClient) -> list[str]:
    response = await client.get("/models")
    response.raise_for_status()

    models = response.json()
    if not models:
        raise Exception("No models found in embedding service.")

    return models


async def get_partially_created_records(
    search_service_client: SearchServiceClient, models: list[str]
) -> list[tuple[str, dict[str, Any]]]:
    response = await asyncio.to_thread(search_service_client.query, build_query(models))

    hits = response.get("hits", {}).get("hits", [])
    if not hits:
        logger.info("No partially created records found.")

    logger.info("Re-embedding task found %s partially created records", len(hits))
    return [(hit["_id"], hit["_source"]) for hit in hits]


def build_query(models: list[str]) -> dict:
    query = {
        "_source": {"includes": ["id", "embedText", *models]},
        "size": 10,  # Limit the result to 10 hits
        "query": {
            "bool": {
                "should": [
                    {"bool": {"must_not": [{"exists": {"field": model}}]}}
                    for model in models
                ]
                + [{"term": {"needs_reembedding": True}}],
                "minimum_should_match": 1,  # Ensures at least one of the conditions is met
            }
        },
    }

    logger.debug("Re-embedding Maintenance query: %s", query)
    return query


async def task_cleaner(interval: str):
    while True:
        logger.info("Cleaning up tasks")
        TaskStatus.clear()
        await aiocron.crontab(interval).next()


async def delta_load_background_task(
    interval: str,
    bucket: storage.Bucket,
    data_preprocessor: DataPreprocessor,
    search_service_client: SearchServiceClient,
    prefix: str,
):
    while True:
        await aiocron.crontab(interval).next()
        logger.info("Running delta load task")
        try:
            await asyncio.to_thread(
                delta_ingest,
                bucket=bucket,
                data_preprocessor=data_preprocessor,
                search_service_client=search_service_client,
                prefix=prefix,
                task_id=f"delta_load_{datetime.datetime.now()}",
            )
        except Exception:
            logger.error("Error during re-embedding task", exc_info=True)


async def delete_background_task(
    interval: str,
    bucket: storage.Bucket,
    search_service_client: SearchServiceClient,
    prefix: str,
):
    while True:
        await aiocron.crontab(interval).next()
        logger.info("Running delete task")
        try:
            await asyncio.to_thread(
                delete_batch,
                bucket=bucket,
                search_service_client=search_service_client,
                prefix=prefix,
            )
        except Exception:
            logger.error("Error during delete task", exc_info=True)
