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
                "loc": ["body", "embedText"],
                "msg": "field required",
                "type": "value_error.missing",
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
        "jina-embeddings-v2-base-de-4096",
        "jina-embeddings-v2-base-de-128",
    }

    assert (
        response_json["embedTextHash"]
        == "a8a2f6ebe286697c527eb35a58b5539532e9b3ae3b64d4eb0a46fb657b41562c"
    )

    assert isinstance(response_json["jina-embeddings-v2-base-de-4096"], list)
    assert len(response_json["jina-embeddings-v2-base-de-4096"]) == 768
    assert all(isinstance(elem, float)for elem in response_json["jina-embeddings-v2-base-de-4096"])

    assert isinstance(response_json["jina-embeddings-v2-base-de-128"], list)
    assert len(response_json["jina-embeddings-v2-base-de-128"]) == 768
    assert all(isinstance(elem, float)for elem in response_json["jina-embeddings-v2-base-de-128"])


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
        "jina-embeddings-v2-base-de-4096",
        "jina-embeddings-v2-base-de-128",
    }

    assert (
        response_json["embedTextHash"]
        == "a8a2f6ebe286697c527eb35a58b5539532e9b3ae3b64d4eb0a46fb657b41562c"
    )

    assert isinstance(response_json["jina-embeddings-v2-base-de-4096"], list)
    assert len(response_json["jina-embeddings-v2-base-de-4096"]) == 768
    assert all(isinstance(elem, float) for elem in response_json["jina-embeddings-v2-base-de-4096"])

    assert isinstance(response_json["jina-embeddings-v2-base-de-128"], list)
    assert len(response_json["jina-embeddings-v2-base-de-128"]) == 768
    assert all(isinstance(elem, float) for elem in response_json["jina-embeddings-v2-base-de-128"])


def test_embedding__with_models(test_client: TestClient):
    response = test_client.post(
        "/embedding",
        json={
            "embedText": "This is a test.",
            "models": ["jina-embeddings-v2-base-de-4096", "unknown-model"],
        },
    )

    response_json = response.json()
    assert response.status_code == 200
    assert set(response_json.keys()) == {
        "embedTextHash",
        "jina-embeddings-v2-base-de-4096",
        "unknown-model",
    }

    assert (
        response_json["embedTextHash"]
        == "a8a2f6ebe286697c527eb35a58b5539532e9b3ae3b64d4eb0a46fb657b41562c"
    )

    assert isinstance(response_json["jina-embeddings-v2-base-de-4096"], list)
    assert len(response_json["jina-embeddings-v2-base-de-4096"]) == 768
    assert all(isinstance(elem, float) for elem in response_json["jina-embeddings-v2-base-de-4096"])

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
                "loc": ["body", "id"],
                "msg": "field required",
                "type": "value_error.missing",
            },
            {
                "loc": ["body", "embedText"],
                "msg": "field required",
                "type": "value_error.missing",
            },
        ]
    }


def test_add_embedding_to_document(httpx_mock, test_client: TestClient):
    httpx_mock.add_response("https://test.io/search/documents/test", json={})

    response = test_client.post(
        "/add-embedding-to-doc", json={"id": "test", "embedText": "This is a test."}
    )

    response_json = response.json()
    assert response.status_code == 200
    assert set(response_json.keys()) == {
        "embedTextHash",
        "jina-embeddings-v2-base-de-4096",
        "jina-embeddings-v2-base-de-128",
        "needs_reembedding",
    }

    assert (
        response_json["embedTextHash"]
        == "a8a2f6ebe286697c527eb35a58b5539532e9b3ae3b64d4eb0a46fb657b41562c"
    )

    assert isinstance(response_json["jina-embeddings-v2-base-de-4096"], list)
    assert len(response_json["jina-embeddings-v2-base-de-4096"]) == 768
    assert all(isinstance(elem, float) for elem in response_json["jina-embeddings-v2-base-de-4096"])

    assert isinstance(response_json["jina-embeddings-v2-base-de-128"], list)
    assert len(response_json["jina-embeddings-v2-base-de-128"]) == 768
    assert all(isinstance(elem, float)for elem in response_json["jina-embeddings-v2-base-de-128"])

    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    assert requests[0].method == "POST"
    assert requests[0].url == "https://test.io/search/documents/test"
    assert requests[0].headers["x-api-key"] == "test_key"
    assert requests[0].content == json.dumps(response_json).encode()


def test_get_models(test_client: TestClient):
    response = test_client.get("/models")
    assert response.status_code == 200
    assert response.json() == [
        "jina-embeddings-v2-base-de-4096",
        "jina-embeddings-v2-base-de-128",
        "pa-service-var-III",
    ]

def test_get_model_config_with_valid_key(test_client: TestClient):
    response = test_client.get("/model_config/wdr")
    assert response.status_code == 200

    response_json = response.json()

    assert set(response_json.keys()) == {
        "c2c_models",
        "u2c_models",
    }

    assert response_json["c2c_models"] == {
        "Jina-A": {
            "display_name": "Jina-A",
            "endpoint": "opensearch://jina-embeddings-v2-base-de-4096",
            "model_name": "jina-embeddings-v2-base-de-4096",
            "model_path": "sentence_transformers/jina-embeddings-v2-base-de-4096",
        },
        "Jina-B": {
            "display_name": "Jina-B",
            "endpoint": "opensearch://jina-embeddings-v2-base-de-128",
            "model_name": "jina-embeddings-v2-base-de-128",
            "model_path": "sentence_transformers/jina-embeddings-v2-base-de-128",
        }
    }

    assert response_json["u2c_models"] == {
        "PA-Service-Var-III": {
            "display_name": "PA-Service-Var-III",
            "endpoint": "https://ts1.dev.mt.ard.hrnmtech.de:8443/ard/recommendation/user2content",
            "model_name": "pa-service-var-III",
        }
    }

def test_get_model_config_with_invalid_key(test_client: TestClient):
    invalid_key = "invalid_key"
    response = test_client.get(f"/model_config/{invalid_key}")
    assert response.status_code == 404

    response_json = response.json()
    assert response_json["detail"] == f"Model configuration not found for key: {invalid_key}"

def test_get_model_config_with_no_key(test_client: TestClient):
    response = test_client.get("/model_config")
    assert response.status_code == 200

    response_json = response.json()
    assert response_json == {
        "c2c_models": {
            "Jina-A": {
                "display_name": "Jina-A",
                "endpoint": "opensearch://jina-embeddings-v2-base-de-4096",
                "model_name": "jina-embeddings-v2-base-de-4096",
                "model_path": "sentence_transformers/jina-embeddings-v2-base-de-4096",
            },
            "Jina-B": {
                "display_name": "Jina-B",
                "endpoint": "opensearch://jina-embeddings-v2-base-de-128",
                "model_name": "jina-embeddings-v2-base-de-128",
                "model_path": "sentence_transformers/jina-embeddings-v2-base-de-128"
            }
        },
        "u2c_models": {
            "PA-Service-Var-III": {
                "display_name": "PA-Service-Var-III",
                "endpoint": "https://ts1.dev.mt.ard.hrnmtech.de:8443/ard/recommendation/user2content",
                "model_name": "pa-service-var-III",
            }
        }
    }
