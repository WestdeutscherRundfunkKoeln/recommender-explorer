import datetime
import json
from pytest_httpx import HTTPXMock

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from src.task_status import TaskStatus
from src.models import BulkIngestTask, BulkIngestTaskStatus
from tests.test_util import MockStorageClient

load_dotenv("tests/test.env")

from src.main import (
    config,
    app,
    storage_client_factory,
)


@pytest.fixture(scope="module")
def test_client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def overwrite_storage_client():
    data = {
        "prod/valid.json": json.dumps(
            {
                "externalid": "test",
                "id": "test",
                "sophoraId": "test",
                "title": "test",
                "description": "test",
                "longDescription": "test",
                "availableFrom": "2023-10-23T23:00:00.000+02:00",
                "availableTo": "2023-10-23T23:00:00.000+02:00",
                "duration": 200,
                "thematicCategories": [],
                "genreCategory": "test",
                "subgenreCategories": [],
                "teaserimage": "test",
                "embedText": "test",
            }
        ),
        "prod/invalid.json": json.dumps(
            {
                "externalid": 1337,
            }
        ),
    }

    mock_client = MockStorageClient(data)
    app.dependency_overrides[storage_client_factory] = lambda: mock_client
    yield mock_client
    app.dependency_overrides.pop(storage_client_factory)


@pytest.fixture
def overwrite_tasks():
    TaskStatus._lifetime_seconds = 0
    TaskStatus.put(
        "exists",
        BulkIngestTask(
            id="exists",
            status=BulkIngestTaskStatus.PREPROCESSING,
            errors=[],
            created_at=datetime.datetime.fromisoformat(
                "2023-10-23T23:00:00.000000+00:00"
            ),
        ),
    )
    yield
    TaskStatus.clear()


def test_upsert_event__with_available_correct_document__no_embedding_in_oss(
    test_client: TestClient, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(
        method="POST",
        headers={"Content-Type": "application/json"},
        json={
            "_index": "sample-index1",
            "_id": "1",
            "_version": 3,
            "result": "updated",
            "_shards": {"total": 2, "successful": 2, "failed": 0},
            "_seq_no": 4,
            "_primary_term": 17,
        },
    )
    httpx_mock.add_response(
        url=config["base_url_search"] + "/documents/test?fields=embedTextHash",
        method="GET",
        json={
            "took": 1,
            "timed_out": False,
            "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
            "_source": {},
        },
    )

    response = test_client.post(
        "/events",
        headers={"Content-Type": "application/json", "eventType": "OBJECT_FINALIZE"},
        json={
            "kind": "storage#object",
            "id": "wdr-recommender-exporter-dev-import/produktion/c65b43ee-cd44-4653-a03d-241ac052c36b.json/1712568938633012",
            "selfLink": "https://www.googleapis.com/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json",
            "name": "prod/valid.json",
            "bucket": "wdr-recommender-exporter-dev-import",
            "generation": "1712568938633012",
            "metageneration": "1",
            "contentType": "application/json",
            "timeCreated": "2024-04-08T09:35:38.666Z",
            "updated": "2024-04-08T09:35:38.666Z",
            "storageClass": "STANDARD",
            "timeStorageClassUpdated": "2024-04-08T09:35:38.666Z",
            "size": "1504",
            "md5Hash": "nUoVmkcgy2xR5l676DzUgw==",
            "mediaLink": "https://storage.googleapis.com/download/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json?generation=1712568938633012&alt=media",
            "crc32c": "+IKxJA==",
            "etag": "CLSu9rmosoUDEAE=",
        },
    )

    assert response.status_code == 200
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    # Request to the search service to check hash
    request = requests[0]
    assert request.method == "GET"
    assert (
        request.url
        == config["base_url_search"] + "/documents/test?fields=embedTextHash"
    )
    assert request.headers["x-api-key"] == "test-key"

    # Request to the search service for upsert
    request = requests[1]
    assert request.method == "POST"
    assert request.url == config["base_url_search"] + "/documents/test"
    assert request.headers["x-api-key"] == "test-key"
    assert json.loads(request.content.decode()) == {
        "externalid": "test",
        "id": "test",
        "cmsId": "test",
        "title": "test",
        "description": "test",
        "longDescription": "test",
        "availableFrom": "2023-10-23T23:00:00+0200",
        "availableTo": "2023-10-23T23:00:00+0200",
        "duration": 200,
        "thematicCategories": [],
        "thematicCategoriesIds": None,
        "thematicCategoriesTitle": None,
        "genreCategory": "test",
        "genreCategoryId": None,
        "subgenreCategories": [],
        "subgenreCategoriesIds": None,
        "subgenreCategoriesTitle": None,
        "teaserimage": "test",
        "geoAvailability": None,
        "embedText": "test",
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
        "uuid": None,
        "needs_reembedding": True,
    }


def test_upsert_event__with_available_correct_document__no_matching_hash(
    test_client: TestClient, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(
        method="POST",
        headers={"Content-Type": "application/json"},
        json={
            "_index": "sample-index1",
            "_id": "1",
            "_version": 3,
            "result": "updated",
            "_shards": {"total": 2, "successful": 2, "failed": 0},
            "_seq_no": 4,
            "_primary_term": 17,
        },
    )
    httpx_mock.add_response(
        url=config["base_url_search"] + "/documents/test?fields=embedTextHash",
        method="GET",
        json={
            "took": 1,
            "timed_out": False,
            "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
            "_source": {
                "embedTextHash": "testHash",
            },
        },
    )

    response = test_client.post(
        "/events",
        headers={"Content-Type": "application/json", "eventType": "OBJECT_FINALIZE"},
        json={
            "kind": "storage#object",
            "id": "wdr-recommender-exporter-dev-import/produktion/c65b43ee-cd44-4653-a03d-241ac052c36b.json/1712568938633012",
            "selfLink": "https://www.googleapis.com/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json",
            "name": "prod/valid.json",
            "bucket": "wdr-recommender-exporter-dev-import",
            "generation": "1712568938633012",
            "metageneration": "1",
            "contentType": "application/json",
            "timeCreated": "2024-04-08T09:35:38.666Z",
            "updated": "2024-04-08T09:35:38.666Z",
            "storageClass": "STANDARD",
            "timeStorageClassUpdated": "2024-04-08T09:35:38.666Z",
            "size": "1504",
            "md5Hash": "nUoVmkcgy2xR5l676DzUgw==",
            "mediaLink": "https://storage.googleapis.com/download/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json?generation=1712568938633012&alt=media",
            "crc32c": "+IKxJA==",
            "etag": "CLSu9rmosoUDEAE=",
        },
    )

    assert response.status_code == 200
    requests = httpx_mock.get_requests()
    assert len(requests) == 2

    # Request to the search service to check hash
    request = requests[0]
    assert request.method == "GET"
    assert (
        request.url
        == config["base_url_search"] + "/documents/test?fields=embedTextHash"
    )
    assert request.headers["x-api-key"] == "test-key"

    # Request to the search service for upsert
    request = requests[1]
    assert request.method == "POST"
    assert request.url == config["base_url_search"] + "/documents/test"
    assert request.headers["x-api-key"] == "test-key"
    assert json.loads(request.content.decode()) == {
        "externalid": "test",
        "id": "test",
        "cmsId": "test",
        "title": "test",
        "description": "test",
        "longDescription": "test",
        "availableFrom": "2023-10-23T23:00:00+0200",
        "availableTo": "2023-10-23T23:00:00+0200",
        "duration": 200,
        "thematicCategories": [],
        "thematicCategoriesIds": None,
        "thematicCategoriesTitle": None,
        "genreCategory": "test",
        "genreCategoryId": None,
        "subgenreCategories": [],
        "subgenreCategoriesIds": None,
        "subgenreCategoriesTitle": None,
        "teaserimage": "test",
        "geoAvailability": None,
        "embedText": "test",
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
        "uuid": None,
        "needs_reembedding": True,
    }


def test_upsert_event__with_available_correct_document__matching_hash(
    test_client: TestClient, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(
        method="POST",
        headers={"Content-Type": "application/json"},
        json={
            "_index": "sample-index1",
            "_id": "1",
            "_version": 3,
            "result": "updated",
            "_shards": {"total": 2, "successful": 2, "failed": 0},
            "_seq_no": 4,
            "_primary_term": 17,
        },
    )
    httpx_mock.add_response(
        url=config["base_url_search"] + "/documents/test?fields=embedTextHash",
        method="GET",
        json={
            "took": 1,
            "timed_out": False,
            "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
            "_source": {
                "embedTextHash": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            },
        },
    )

    response = test_client.post(
        "/events",
        headers={"Content-Type": "application/json", "eventType": "OBJECT_FINALIZE"},
        json={
            "kind": "storage#object",
            "id": "wdr-recommender-exporter-dev-import/produktion/c65b43ee-cd44-4653-a03d-241ac052c36b.json/1712568938633012",
            "selfLink": "https://www.googleapis.com/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json",
            "name": "prod/valid.json",
            "bucket": "wdr-recommender-exporter-dev-import",
            "generation": "1712568938633012",
            "metageneration": "1",
            "contentType": "application/json",
            "timeCreated": "2024-04-08T09:35:38.666Z",
            "updated": "2024-04-08T09:35:38.666Z",
            "storageClass": "STANDARD",
            "timeStorageClassUpdated": "2024-04-08T09:35:38.666Z",
            "size": "1504",
            "md5Hash": "nUoVmkcgy2xR5l676DzUgw==",
            "mediaLink": "https://storage.googleapis.com/download/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json?generation=1712568938633012&alt=media",
            "crc32c": "+IKxJA==",
            "etag": "CLSu9rmosoUDEAE=",
        },
    )

    assert response.status_code == 200
    requests = httpx_mock.get_requests()
    assert len(requests) == 2

    # Request to the search service to check hash
    request = requests[0]
    assert request.method == "GET"
    assert (
        request.url
        == config["base_url_search"] + "/documents/test?fields=embedTextHash"
    )
    assert request.headers["x-api-key"] == "test-key"

    # Request to the search service for upsert
    request = requests[1]
    assert request.method == "POST"
    assert request.url == config["base_url_search"] + "/documents/test"
    assert request.headers["x-api-key"] == "test-key"
    assert json.loads(request.content.decode()) == {
        "externalid": "test",
        "id": "test",
        "cmsId": "test",
        "title": "test",
        "description": "test",
        "longDescription": "test",
        "availableFrom": "2023-10-23T23:00:00+0200",
        "availableTo": "2023-10-23T23:00:00+0200",
        "duration": 200,
        "thematicCategories": [],
        "thematicCategoriesIds": None,
        "thematicCategoriesTitle": None,
        "genreCategory": "test",
        "genreCategoryId": None,
        "subgenreCategories": [],
        "subgenreCategoriesIds": None,
        "subgenreCategoriesTitle": None,
        "teaserimage": "test",
        "geoAvailability": None,
        "embedText": "test",
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
        "uuid": None,
        "needs_reembedding": False,
    }


def test_upsert_event_no_document_found(
    test_client: TestClient,
    httpx_mock: HTTPXMock,
    overwrite_storage_client: MockStorageClient,
):
    response = test_client.post(
        "/events",
        headers={"Content-Type": "application/json", "eventType": "OBJECT_FINALIZE"},
        json={
            "kind": "storage#object",
            "id": "wdr-recommender-exporter-dev-import/produktion/c65b43ee-cd44-4653-a03d-241ac052c36b.json/1712568938633012",
            "selfLink": "https://www.googleapis.com/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json",
            "name": "prod/nonexistent.json",
            "bucket": "wdr-recommender-exporter-dev-import",
            "generation": "1712568938633012",
            "metageneration": "1",
            "contentType": "application/json",
            "timeCreated": "2024-04-08T09:35:38.666Z",
            "updated": "2024-04-08T09:35:38.666Z",
            "storageClass": "STANDARD",
            "timeStorageClassUpdated": "2024-04-08T09:35:38.666Z",
            "size": "1504",
            "md5Hash": "nUoVmkcgy2xR5l676DzUgw==",
            "mediaLink": "https://storage.googleapis.com/download/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json?generation=1712568938633012&alt=media",
            "crc32c": "+IKxJA==",
            "etag": "CLSu9rmosoUDEAE=",
        },
    )

    assert response.status_code == 200
    assert response.json() == "Blob not found"
    assert len(httpx_mock.get_requests()) == 0


def test_upsert_event_general_error(
    test_client: TestClient,
    httpx_mock: HTTPXMock,
    overwrite_storage_client: MockStorageClient,
):
    response = test_client.post(
        "/events",
        headers={"Content-Type": "application/json", "eventType": "OBJECT_FINALIZE"},
        json={
            "kind": "storage#object",
            "id": "wdr-recommender-exporter-dev-import/produktion/c65b43ee-cd44-4653-a03d-241ac052c36b.json/1712568938633012",
            "selfLink": "https://www.googleapis.com/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json",
            "name": "error",
            "bucket": "wdr-recommender-exporter-dev-import",
            "generation": "1712568938633012",
            "metageneration": "1",
            "contentType": "application/json",
            "timeCreated": "2024-04-08T09:35:38.666Z",
            "updated": "2024-04-08T09:35:38.666Z",
            "storageClass": "STANDARD",
            "timeStorageClassUpdated": "2024-04-08T09:35:38.666Z",
            "size": "1504",
            "md5Hash": "nUoVmkcgy2xR5l676DzUgw==",
            "mediaLink": "https://storage.googleapis.com/download/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json?generation=1712568938633012&alt=media",
            "crc32c": "+IKxJA==",
            "etag": "CLSu9rmosoUDEAE=",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"detail": "Test error"}
    assert len(httpx_mock.get_requests()) == 0

    bucket_data = overwrite_storage_client.bucket("test_dead_letter_bucket").data
    blob = next((blob for blob in bucket_data if blob.startswith("20")))
    assert blob is not None
    uploaded_data = json.loads(bucket_data[blob].data)
    assert uploaded_data["name"] == "error"
    assert uploaded_data["bucket"] == "wdr-recommender-exporter-dev-import"
    assert uploaded_data["event_type"] == "OBJECT_FINALIZE"
    assert uploaded_data["exception"] == "Test error"
    assert uploaded_data["url"] == "http://testserver/events"


def test_upsert_event_invalid_document(
    test_client: TestClient,
    httpx_mock: HTTPXMock,
    overwrite_storage_client: MockStorageClient,
):
    response = test_client.post(
        "/events",
        headers={"Content-Type": "application/json", "eventType": "OBJECT_FINALIZE"},
        json={
            "kind": "storage#object",
            "id": "wdr-recommender-exporter-dev-import/produktion/c65b43ee-cd44-4653-a03d-241ac052c36b.json/1712568938633012",
            "selfLink": "https://www.googleapis.com/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json",
            "name": "prod/invalid.json",
            "bucket": "wdr-recommender-exporter-dev-import",
            "generation": "1712568938633012",
            "metageneration": "1",
            "contentType": "application/json",
            "timeCreated": "2024-04-08T09:35:38.666Z",
            "updated": "2024-04-08T09:35:38.666Z",
            "storageClass": "STANDARD",
            "timeStorageClassUpdated": "2024-04-08T09:35:38.666Z",
            "size": "1504",
            "md5Hash": "nUoVmkcgy2xR5l676DzUgw==",
            "mediaLink": "https://storage.googleapis.com/download/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json?generation=1712568938633012&alt=media",
            "crc32c": "+IKxJA==",
            "etag": "CLSu9rmosoUDEAE=",
        },
    )

    assert response.status_code == 200
    assert len(httpx_mock.get_requests()) == 0

    bucket_data = overwrite_storage_client.bucket("test_dead_letter_bucket").data
    blob = next((blob for blob in bucket_data if blob.startswith("20")))
    uploaded_data = json.loads(bucket_data[blob].data)
    assert uploaded_data["name"] == "prod/invalid.json"
    assert uploaded_data["bucket"] == "wdr-recommender-exporter-dev-import"
    assert uploaded_data["event_type"] == "OBJECT_FINALIZE"
    assert (
        uploaded_data["exception"]
        == "12 validation errors for RecoExplorerItem\nexternalid\n  Input should be a valid string [type=string_type, input_value=1337, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.9/v/string_type\nid\n  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]\n    For further information visit https://errors.pydantic.dev/2.9/v/string_type\ncmsId\n  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]\n    For further information visit https://errors.pydantic.dev/2.9/v/string_type\ntitle\n  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]\n    For further information visit https://errors.pydantic.dev/2.9/v/string_type\ndescription\n  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]\n    For further information visit https://errors.pydantic.dev/2.9/v/string_type\nlongDescription\n  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]\n    For further information visit https://errors.pydantic.dev/2.9/v/string_type\navailableFrom\n  Input should be a valid datetime [type=datetime_type, input_value=None, input_type=NoneType]\n    For further information visit https://errors.pydantic.dev/2.9/v/datetime_type\navailableTo\n  Input should be a valid datetime [type=datetime_type, input_value=None, input_type=NoneType]\n    For further information visit https://errors.pydantic.dev/2.9/v/datetime_type\nthematicCategories\n  Input should be a valid list [type=list_type, input_value=None, input_type=NoneType]\n    For further information visit https://errors.pydantic.dev/2.9/v/list_type\nsubgenreCategories\n  Input should be a valid list [type=list_type, input_value=None, input_type=NoneType]\n    For further information visit https://errors.pydantic.dev/2.9/v/list_type\nteaserimage\n  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]\n    For further information visit https://errors.pydantic.dev/2.9/v/string_type\nembedText\n  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]\n    For further information visit https://errors.pydantic.dev/2.9/v/string_type"
    )
    assert uploaded_data["url"] == "http://testserver/events"


def test_delete_event_with_available_correct_document(
    test_client: TestClient, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(
        headers={"Content-Type": "application/json"},
        json={
            "_index": "sample-index1",
            "_id": "1",
            "_version": 3,
            "result": "deleted",
            "_shards": {"total": 2, "successful": 2, "failed": 0},
            "_seq_no": 4,
            "_primary_term": 17,
        },
    )

    response = test_client.post(
        "/events",
        headers={"Content-Type": "application/json", "eventType": "OBJECT_DELETE"},
        json={
            "kind": "storage#object",
            "id": "wdr-recommender-exporter-dev-import/produktion/c65b43ee-cd44-4653-a03d-241ac052c36b.json/1712568938633012",
            "selfLink": "https://www.googleapis.com/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json",
            "name": "prod/valid.json",
            "bucket": "wdr-recommender-exporter-dev-import",
            "generation": "1712568938633012",
            "metageneration": "1",
            "contentType": "application/json",
            "timeCreated": "2024-04-08T09:35:38.666Z",
            "updated": "2024-04-08T09:35:38.666Z",
            "storageClass": "STANDARD",
            "timeStorageClassUpdated": "2024-04-08T09:35:38.666Z",
            "size": "1504",
            "md5Hash": "nUoVmkcgy2xR5l676DzUgw==",
            "mediaLink": "https://storage.googleapis.com/download/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json?generation=1712568938633012&alt=media",
            "crc32c": "+IKxJA==",
            "etag": "CLSu9rmosoUDEAE=",
        },
    )

    assert response.status_code == 200
    requests = httpx_mock.get_requests()
    assert len(requests) == 1

    # Request to the search service
    request = requests[0]
    assert request.method == "DELETE"
    assert request.url == config["base_url_search"] + "/documents/valid"
    assert request.headers["x-api-key"] == "test-key"


def test_delete_event_with_missing_document(
    test_client: TestClient, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(
        status_code=404,
    )

    response = test_client.post(
        "/events",
        headers={"Content-Type": "application/json", "eventType": "OBJECT_DELETE"},
        json={
            "kind": "storage#object",
            "id": "wdr-recommender-exporter-dev-import/produktion/c65b43ee-cd44-4653-a03d-241ac052c36b.json/1712568938633012",
            "selfLink": "https://www.googleapis.com/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json",
            "name": "prod/valid.json",
            "bucket": "wdr-recommender-exporter-dev-import",
            "generation": "1712568938633012",
            "metageneration": "1",
            "contentType": "application/json",
            "timeCreated": "2024-04-08T09:35:38.666Z",
            "updated": "2024-04-08T09:35:38.666Z",
            "storageClass": "STANDARD",
            "timeStorageClassUpdated": "2024-04-08T09:35:38.666Z",
            "size": "1504",
            "md5Hash": "nUoVmkcgy2xR5l676DzUgw==",
            "mediaLink": "https://storage.googleapis.com/download/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json?generation=1712568938633012&alt=media",
            "crc32c": "+IKxJA==",
            "etag": "CLSu9rmosoUDEAE=",
        },
    )

    assert response.status_code == 200
    assert (
        response.json()
        == "Delete event for valid is ignored, as the entry is not found in OSS"
    )
    requests = httpx_mock.get_requests()
    assert len(requests) == 1

    # Request to the search service
    request = requests[0]
    assert request.method == "DELETE"
    assert request.url == config["base_url_search"] + "/documents/valid"
    assert request.headers["x-api-key"] == "test-key"


def test_delete_event_with_general_error(
    test_client: TestClient,
    httpx_mock: HTTPXMock,
    overwrite_storage_client: MockStorageClient,
):
    httpx_mock.add_response(
        status_code=500,
    )

    response = test_client.post(
        "/events",
        headers={"Content-Type": "application/json", "eventType": "OBJECT_DELETE"},
        json={
            "kind": "storage#object",
            "id": "wdr-recommender-exporter-dev-import/produktion/c65b43ee-cd44-4653-a03d-241ac052c36b.json/1712568938633012",
            "selfLink": "https://www.googleapis.com/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json",
            "name": "prod/valid.json",
            "bucket": "wdr-recommender-exporter-dev-import",
            "generation": "1712568938633012",
            "metageneration": "1",
            "contentType": "application/json",
            "timeCreated": "2024-04-08T09:35:38.666Z",
            "updated": "2024-04-08T09:35:38.666Z",
            "storageClass": "STANDARD",
            "timeStorageClassUpdated": "2024-04-08T09:35:38.666Z",
            "size": "1504",
            "md5Hash": "nUoVmkcgy2xR5l676DzUgw==",
            "mediaLink": "https://storage.googleapis.com/download/storage/v1/b/wdr-recommender-exporter-dev-import/o/produktion%2Fc65b43ee-cd44-4653-a03d-241ac052c36b.json?generation=1712568938633012&alt=media",
            "crc32c": "+IKxJA==",
            "etag": "CLSu9rmosoUDEAE=",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "detail": "Server error '500 Internal Server Error' for url 'https://test.io/search/documents/valid'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/500"
    }

    bucket_data = overwrite_storage_client.bucket("test_dead_letter_bucket").data
    blob = next((blob for blob in bucket_data if blob.startswith("20")))
    assert blob is not None
    uploaded_data = json.loads(bucket_data[blob].data)
    assert uploaded_data["name"] == "prod/valid.json"
    assert uploaded_data["bucket"] == "wdr-recommender-exporter-dev-import"
    assert uploaded_data["event_type"] == "OBJECT_DELETE"
    assert (
        uploaded_data["exception"]
        == "Server error '500 Internal Server Error' for url 'https://test.io/search/documents/valid'\nFor more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/500"
    )
    assert uploaded_data["url"] == "http://testserver/events"

    requests = httpx_mock.get_requests()
    assert len(requests) == 1

    # Request to the search service
    request = requests[0]
    assert request.method == "DELETE"
    assert request.url == config["base_url_search"] + "/documents/valid"
    assert request.headers["x-api-key"] == "test-key"


def test_bulk_ingest__with_validation_error(
    test_client: TestClient, httpx_mock: HTTPXMock
):
    httpx_mock.add_response(
        url=config["base_url_search"] + "/documents",
        json={"status": "ok"},
        status_code=200,
    )
    httpx_mock.add_response(
        url=config["base_url_search"] + "/documents/test?fields=embedTextHash",
        method="GET",
        json={
            "took": 1,
            "timed_out": False,
            "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
            "_source": {},
        },
    )

    response = test_client.post(
        "/ingest-multiple-items",
        json={
            "bucket": "wdr-recommender-exporter-dev-import",
            "prefix": "prod/",
        },
    )

    assert response.status_code == 202
    task_id = response.json()["task_id"]

    requests = httpx_mock.get_requests()
    assert len(requests) == 2

    # Request to the search service
    request = requests[0]
    assert request.method == "GET"
    assert (
        request.url
        == config["base_url_search"] + "/documents/test?fields=embedTextHash"
    )
    assert request.headers["x-api-key"] == "test-key"

    request = requests[1]
    assert request.method == "POST"
    assert request.url == config["base_url_search"] + "/documents"
    assert request.headers["x-api-key"] == "test-key"
    assert json.loads(request.content.decode()) == {
        "test": {
            "externalid": "test",
            "id": "test",
            "cmsId": "test",
            "title": "test",
            "description": "test",
            "longDescription": "test",
            "availableFrom": "2023-10-23T23:00:00+0200",
            "availableTo": "2023-10-23T23:00:00+0200",
            "duration": 200,
            "thematicCategories": [],
            "thematicCategoriesIds": None,
            "thematicCategoriesTitle": None,
            "genreCategory": "test",
            "genreCategoryId": None,
            "subgenreCategories": [],
            "subgenreCategoriesIds": None,
            "subgenreCategoriesTitle": None,
            "teaserimage": "test",
            "geoAvailability": None,
            "embedText": "test",
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
            "uuid": None,
            "needs_reembedding": True,
        }
    }
    response = test_client.get(
        f"/tasks/{task_id}",
    )
    assert response.status_code == 200
    task = response.json()["task"]
    assert task["id"] == task_id
    assert task["status"] == "COMPLETED"
    assert task["completed_items"] == 1
    assert task["failed_items"] == 1
    assert len(task["errors"]) == 1
    assert task["errors"][0].startswith("Validation error")


def test_bulk_ingest__with_general_error(test_client, httpx_mock):
    response = test_client.post(
        "/ingest-multiple-items",
        json={
            "bucket": "test",
            "prefix": "raise_error/",
        },
    )

    assert response.status_code == 202
    task_id = response.json()["task_id"]

    assert len(httpx_mock.get_requests()) == 0

    response = test_client.get(
        f"/tasks/{task_id}",
    )
    assert response.status_code == 200
    task = response.json()["task"]
    assert task["id"] == task_id
    assert task["status"] == "FAILED"
    assert task["errors"] == ["Test error"]
    assert task["completed_items"] == 0
    assert task["failed_items"] == 0


def test_get_task__exists(test_client: TestClient, overwrite_tasks):
    response = test_client.get("/tasks/exists")

    assert response.status_code == 200
    assert response.json() == {
        "task": {
            "completed_at": None,
            "id": "exists",
            "status": "PREPROCESSING",
            "errors": [],
            "created_at": "2023-10-23T23:00:00Z",
            "completed_items": 0,
            "failed_items": 0,
        }
    }


def test_get_task__not_exists(test_client: TestClient, overwrite_tasks):
    response = test_client.get("/tasks/_not_exists")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_get_tasks(test_client: TestClient, overwrite_tasks):
    response = test_client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == {
        "tasks": [
            {
                "id": "exists",
                "status": "PREPROCESSING",
                "errors": [],
                "created_at": "2023-10-23T23:00:00Z",
                "completed_at": None,
                "completed_items": 0,
                "failed_items": 0,
            }
        ]
    }
