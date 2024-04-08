from fastapi.testclient import TestClient
from dotenv import load_dotenv
import json
import os
from google.api_core.exceptions import GoogleAPICallError
import pytest

load_dotenv("tests/test.env")


@pytest.fixture(scope="module")
def test_client():
    from src.main import app

    return TestClient(app)


class MockStorageClient:
    def __init__(self, data: dict[str, str]):
        self.data = data
        self.bucket_name = ""
        self.blob_name = ""

    def bucket(self, bucket_name: str):
        self.bucket_name = bucket_name
        return self

    def blob(self, blob_name: str):
        self.blob_name = blob_name
        return self

    def download_as_text(self) -> str:
        data = self.data.get(self.blob_name)
        if data is None:
            raise GoogleAPICallError("Blob not found")
        return data


@pytest.fixture(scope="module", autouse=True)
def overwrite_storage_client():
    from src.main import app, get_storage_client

    data = {
        "prod/valid.json": json.dumps(
            {
                "externalid": "test",
                "id": "test",
                "title": "test",
                "description": "test",
                "longDescription": "test",
                "availableFrom": "2023-10-23T23:00:00.000+02:00",
                "availableTo": "2023-10-23T23:00:00.000+02:00",
                "duration": 200,
                "thematicCategories": [],
                "genreCategory": [],
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

    app.dependency_overrides[get_storage_client] = lambda: MockStorageClient(data)
    yield
    app.dependency_overrides.pop(get_storage_client)


def test_upsert_event_with_available_correct_document(test_client, httpx_mock):
    httpx_mock.add_response(
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

    response = test_client.post(
        "/ingest-single-item",
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

    # Request to the embedding service
    request = requests[0]
    assert request.method == "POST"
    assert request.url == os.getenv("URL_EMBEDDING")
    assert request.content == json.dumps({"id": "test", "embedText": "test"}).encode()

    # Request to the search service
    request = requests[1]
    assert request.method == "POST"
    assert request.url == os.getenv("URL_SEARCH_SINGLE")
    assert (
        request.content
        == json.dumps(
            {
                "externalid": "test",
                "id": "test",
                "title": "test",
                "description": "test",
                "longDescription": "test",
                "availableFrom": 1698094800.0,
                "availableTo": 1698094800.0,
                "duration": None,
                "thematicCategories": [],
                "thematicCategoriesIds": None,
                "thematicCategoriesTitle": None,
                "genreCategory": [],
                "genreCategoryId": None,
                "subgenreCategories": [],
                "subgenreCategoriesIds": None,
                "subgenreCategoriesTitle": None,
                "teaserimage": "test",
                "geoAvailability": None,
                "embedText": "test",
                "embedTextHash": None,
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
            }
        ).encode()
    )


def test_upsert_event_no_document_found(test_client):
    response = test_client.post(
        "/ingest-single-item",
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

    assert response.status_code == 400
    assert response.json() == {"detail": "Blob not found"}


def test_upsert_event_invalid_document(test_client):
    response = test_client.post(
        "/ingest-single-item",
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

    assert response.status_code == 422
