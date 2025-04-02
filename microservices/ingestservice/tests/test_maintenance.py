import json

import pytest
from envyaml import EnvYAML
from pytest_httpx import HTTPXMock
from src.clients import SearchServiceClient
from src.ingest import delete_batch, delta_ingest
from src.maintenance import embed_partially_created_records
from src.preprocess_data import DataPreprocessor
from src.task_status import TaskStatus
from tests.test_util import MockBucket


@pytest.fixture(scope="module")
def config():
    return EnvYAML("tests/test_config.yaml")


@pytest.fixture(scope="module")
def search_service_client(config):
    return SearchServiceClient.from_config(config)


@pytest.mark.asyncio
async def test_reembedding_task(
    httpx_mock: HTTPXMock, config: EnvYAML, search_service_client: SearchServiceClient
):
    httpx_mock.add_response(
        url=f"{config['base_url_embedding']}/models", json=["model_1", "model_2"]
    )
    httpx_mock.add_response(
        url=f"{config['base_url_embedding']}/add-embedding-to-doc", json={}
    )
    httpx_mock.add_response(
        url=f"{config['base_url_search']}/query",
        json={
            "hits": {
                "hits": [
                    {"_id": "none", "_source": {"embedText": "test"}},
                    {
                        "_id": "model_1",
                        "_source": {"embedText": "test", "model_1": [1, 1]},
                    },
                    {
                        "_id": "model_2",
                        "_source": {"embedText": "test", "model_2": [2, 2]},
                    },
                ]
            }
        },
    )
    await embed_partially_created_records(search_service_client, config)
    requests = httpx_mock.get_requests()
    assert len(requests) == 5

    request = requests[0]
    assert request.method == "GET"
    assert request.url == f"{config['base_url_embedding']}/models"
    assert request.headers["x-api-key"] == config["api_key"]

    request = requests[1]
    assert request.method == "POST"
    assert request.url == f"{config['base_url_search']}/query"
    assert request.headers["x-api-key"] == config["api_key"]
    assert json.loads(request.content.decode()) == {
        "_source": {"includes": ["id", "embedText", "model_1", "model_2"]},
        "query": {
            "bool": {
                "minimum_should_match": 1,
                "should": [
                    {"bool": {"must_not": [{"exists": {"field": "model_1"}}]}},
                    {"bool": {"must_not": [{"exists": {"field": "model_2"}}]}},
                    {"term": {"needs_reembedding": True}},
                ],
            }
        },
        "size": 10,
    }

    request = requests[2]
    assert request.method == "POST"
    assert request.url == f"{config['base_url_embedding']}/add-embedding-to-doc"
    assert request.headers["x-api-key"] == config["api_key"]
    assert json.loads(request.content.decode()) == {
        "embedText": "test",
        "id": "none",
        "models": ["model_1", "model_2"],
    }

    request = requests[3]
    assert request.method == "POST"
    assert request.url == f"{config['base_url_embedding']}/add-embedding-to-doc"
    assert request.headers["x-api-key"] == config["api_key"]
    assert json.loads(request.content.decode()) == {
        "embedText": "test",
        "id": "model_1",
        "models": ["model_2"],
    }

    request = requests[4]
    assert request.method == "POST"
    assert request.url == f"{config['base_url_embedding']}/add-embedding-to-doc"
    assert request.headers["x-api-key"] == config["api_key"]
    assert json.loads(request.content.decode()) == {
        "embedText": "test",
        "id": "model_2",
        "models": ["model_1"],
    }


def test_delta_ingest(
    httpx_mock: HTTPXMock, config: EnvYAML, search_service_client: SearchServiceClient
):
    httpx_mock.add_response(
        url=f"{config['base_url_search']}/scan",
        json=[{"_id": "test1"}, {"_id": "test3"}],
        status_code=200,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{config['base_url_search']}/documents",
        json={},
        status_code=200,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{config['base_url_search']}/documents/test2?fields=embedTextHash",
        json={
            "hits": {
                "total": {"value": 1},
                "hits": [{"_source": {"embedTextHash": "test2"}}],
            }
        },
        status_code=200,
    )
    data_preprocessor = DataPreprocessor(config)
    bucket = MockBucket(
        data={
            "test/test1.json": json.dumps(
                {
                    "externalid": "test1",
                    "id": "test1",
                    "sophoraId": "test1",
                    "title": "test1",
                    "description": "test1",
                    "longDescription": "test1",
                    "availableFrom": "2023-10-23T23:00:00.000+02:00",
                    "availableTo": "2023-10-23T23:00:00.000+02:00",
                    "duration": 200,
                    "thematicCategories": [],
                    "genreCategory": "test1",
                    "subgenreCategories": [],
                    "teaserimage": "test1",
                    "embedText": "test1",
                }
            ),
            "test/test2.json": json.dumps(
                {
                    "externalid": "test2",
                    "id": "test2",
                    "sophoraId": "test2",
                    "title": "test2",
                    "description": "test2",
                    "longDescription": "test2",
                    "availableFrom": "2023-10-23T23:00:00.000+02:00",
                    "availableTo": "2023-10-23T23:00:00.000+02:00",
                    "duration": 200,
                    "thematicCategories": [],
                    "genreCategory": "test2",
                    "subgenreCategories": [],
                    "teaserimage": "test2",
                    "embedText": "test2",
                }
            ),
            "test/test_invalid.json": json.dumps(
                {
                    "id": "test_invalid",
                }
            ),
        }
    )
    log_bucket = MockBucket({})

    delta_ingest(
        bucket=bucket,
        data_preprocessor=data_preprocessor,
        search_service_client=search_service_client,
        prefix="test/",
        task_id="test",
        log_bucket=log_bucket,
    )

    task_status = TaskStatus.get("test")
    assert task_status is not None
    assert task_status.status == "COMPLETED"
    assert len(task_status.errors) == 1
    assert task_status.errors[0].startswith("Validation error")

    data_in_bucket = json.loads(log_bucket.blob("test.json").data)
    assert data_in_bucket["status"] == "COMPLETED"
    assert len(data_in_bucket["errors"]) == 1
    assert data_in_bucket["errors"][0].startswith("Validation error")

    requests = httpx_mock.get_requests()
    assert len(requests) == 3

    request = requests[0]
    assert request.method == "POST"
    assert request.url == f"{config['base_url_search']}/scan"
    assert request.headers["x-api-key"] == config["api_key"]
    assert json.loads(request.content.decode()) == {
        "_source": False,
        "query": {"match_all": {}},
    }

    request = requests[1]
    assert request.method == "GET"
    assert (
        request.url
        == f"{config['base_url_search']}/documents/test2?fields=embedTextHash"
    )
    assert request.headers["x-api-key"] == config["api_key"]

    request = requests[2]
    assert request.method == "POST"
    assert request.url == f"{config['base_url_search']}/documents"
    assert request.headers["x-api-key"] == config["api_key"]
    assert json.loads(request.content.decode()) == {
        "test2": {
            "externalid": "test2",
            "id": "test2",
            "cmsId": "test2",
            "title": "test2",
            "description": "test2",
            "longDescription": "test2",
            "availableFrom": "2023-10-23T23:00:00+0200",
            "availableTo": "2023-10-23T23:00:00+0200",
            "duration": 200,
            "thematicCategories": [],
            "thematicCategoriesIds": None,
            "thematicCategoriesTitle": None,
            "genreCategory": "test2",
            "genreCategoryId": None,
            "subgenreCategories": [],
            "subgenreCategoriesIds": None,
            "subgenreCategoriesTitle": None,
            "teaserimage": "test2",
            "geoAvailability": None,
            "embedText": "test2",
            "episodeNumber": "",
            "hasAudioDescription": False,
            "hasDefaultVersion": False,
            "hasSignLanguage": False,
            "hasSubtitles": False,
            "isChildContent": False,
            "isOnlineOnly": False,
            "isOriginalLanguage": False,
            "producer": "",
            "publisherId": "",
            "seasonNumber": "",
            "sections": "",
            "showCrid": "",
            "showId": "",
            "showTitel": "",
            "showType": "",
            "needs_reembedding": True,
            "uuid": None,
        }
    }


def test_delete(
    httpx_mock: HTTPXMock, config: EnvYAML, search_service_client: SearchServiceClient
):
    httpx_mock.add_response(
        url=f"{config['base_url_search']}/scan",
        json=[{"_id": "test1"}, {"_id": "test3"}],
        status_code=200,
    )
    httpx_mock.add_response(
        method="DELETE",
        url=f"{config['base_url_search']}/documents",
        status_code=200,
    )
    bucket = MockBucket(
        data={
            "test/test1.json": json.dumps(
                {
                    "id": "test1",
                }
            ),
            "test/test2.json": json.dumps(
                {
                    "id": "test2",
                }
            ),
        }
    )

    delete_batch(
        bucket=bucket, prefix="test/", search_service_client=search_service_client
    )

    requests = httpx_mock.get_requests()
    assert len(requests) == 2

    request = requests[0]
    assert request.method == "POST"
    assert request.url == f"{config['base_url_search']}/scan"
    assert request.headers["x-api-key"] == config["api_key"]
    assert json.loads(request.content.decode()) == {
        "_source": False,
        "query": {"match_all": {}},
    }

    request = requests[1]
    assert request.method == "DELETE"
    assert request.url == f"{config['base_url_search']}/documents"
    assert request.headers["x-api-key"] == config["api_key"]
    assert json.loads(request.content.decode()) == ["test3"]
