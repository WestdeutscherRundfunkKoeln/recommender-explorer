import json
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client(monkeypatch):
    monkeypatch.setenv("CONFIG_FILE", "tests/config.yaml")
    from src.main import app

    return TestClient(app)


def test_embedding__malformed_request(test_client: TestClient):
    response = test_client.post(
        "/embedding",
        json={
            "malformed": "request",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "input": {"malformed": "request"},
                "loc": ["body", "embedText"],
                "msg": "Field required",
                "type": "missing",
            }
        ]
    }


def test_embedding__no_models(test_client: TestClient):
    response = test_client.post(
        "/embedding",
        json={
            "embedText": "This is a test.",
        },
    )

    response_json = response.json()
    assert response.status_code == 200
    assert set(response_json.keys()) == {
        "embedTextHash",
        "all-MiniLM-L6-v2",
        "distiluse-base-multilingual-cased-v1",
    }

    assert (
        response_json["embedTextHash"]
        == "a8a2f6ebe286697c527eb35a58b5539532e9b3ae3b64d4eb0a46fb657b41562c"
    )

    assert isinstance(response_json["all-MiniLM-L6-v2"], list)
    assert len(response_json["all-MiniLM-L6-v2"]) == 384
    assert all(isinstance(elem, float) for elem in response_json["all-MiniLM-L6-v2"])

    assert isinstance(response_json["distiluse-base-multilingual-cased-v1"], list)
    assert len(response_json["distiluse-base-multilingual-cased-v1"]) == 512
    assert all(
        isinstance(elem, float)
        for elem in response_json["distiluse-base-multilingual-cased-v1"]
    )


def test_embedding__empty_models(test_client: TestClient):
    response = test_client.post(
        "/embedding",
        json={
            "embedText": "This is a test.",
            "models": [],
        },
    )

    response_json = response.json()
    assert response.status_code == 200
    assert set(response_json.keys()) == {
        "embedTextHash",
        "all-MiniLM-L6-v2",
        "distiluse-base-multilingual-cased-v1",
    }

    assert (
        response_json["embedTextHash"]
        == "a8a2f6ebe286697c527eb35a58b5539532e9b3ae3b64d4eb0a46fb657b41562c"
    )

    assert isinstance(response_json["all-MiniLM-L6-v2"], list)
    assert len(response_json["all-MiniLM-L6-v2"]) == 384
    assert all(isinstance(elem, float) for elem in response_json["all-MiniLM-L6-v2"])

    assert isinstance(response_json["distiluse-base-multilingual-cased-v1"], list)
    assert len(response_json["distiluse-base-multilingual-cased-v1"]) == 512
    assert all(
        isinstance(elem, float)
        for elem in response_json["distiluse-base-multilingual-cased-v1"]
    )


def test_embedding__with_models(test_client: TestClient):
    response = test_client.post(
        "/embedding",
        json={
            "embedText": "This is a test.",
            "models": ["all-MiniLM-L6-v2", "unknown-model"],
        },
    )

    response_json = response.json()
    assert response.status_code == 200
    assert set(response_json.keys()) == {
        "embedTextHash",
        "all-MiniLM-L6-v2",
        "unknown-model",
    }

    assert (
        response_json["embedTextHash"]
        == "a8a2f6ebe286697c527eb35a58b5539532e9b3ae3b64d4eb0a46fb657b41562c"
    )

    assert isinstance(response_json["all-MiniLM-L6-v2"], list)
    assert len(response_json["all-MiniLM-L6-v2"]) == 384
    assert all(isinstance(elem, float) for elem in response_json["all-MiniLM-L6-v2"])

    assert response_json["unknown-model"] == "unknown model!"


def test_add_embedding_to_document__malformed_request(test_client: TestClient):
    response = test_client.post(
        "/add-embedding-to-doc",
        json={
            "malformed": "request",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "input": {"malformed": "request"},
                "loc": ["body", "id"],
                "msg": "Field required",
                "type": "missing",
            },
            {
                "input": {"malformed": "request"},
                "loc": ["body", "embedText"],
                "msg": "Field required",
                "type": "missing",
            },
        ]
    }


def test_add_embedding_to_document(httpx_mock, test_client: TestClient):
    httpx_mock.add_response("https://test.io/search/create-single-document", json={})

    response = test_client.post(
        "/add-embedding-to-doc", json={"id": "test", "embedText": "This is a test."}
    )

    response_json = response.json()
    assert response.status_code == 200
    assert set(response_json.keys()) == {
        "embedTextHash",
        "all-MiniLM-L6-v2",
        "distiluse-base-multilingual-cased-v1",
        "id",
    }
    assert response_json["id"] == "test"

    assert (
        response_json["embedTextHash"]
        == "a8a2f6ebe286697c527eb35a58b5539532e9b3ae3b64d4eb0a46fb657b41562c"
    )

    assert isinstance(response_json["all-MiniLM-L6-v2"], list)
    assert len(response_json["all-MiniLM-L6-v2"]) == 384
    assert all(isinstance(elem, float) for elem in response_json["all-MiniLM-L6-v2"])

    assert isinstance(response_json["distiluse-base-multilingual-cased-v1"], list)
    assert len(response_json["distiluse-base-multilingual-cased-v1"]) == 512
    assert all(
        isinstance(elem, float)
        for elem in response_json["distiluse-base-multilingual-cased-v1"]
    )

    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    assert requests[0].method == "POST"
    assert requests[0].url == "https://test.io/search/create-single-document"
    assert requests[0].headers["x-api-key"] == "test_key"
    assert requests[0].content == json.dumps(response_json).encode()
