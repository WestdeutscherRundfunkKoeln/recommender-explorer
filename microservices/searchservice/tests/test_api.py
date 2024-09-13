from time import sleep
import pytest
from opensearchpy import OpenSearch, RequestError
from src.oss_accessor import OssAccessor
from fastapi.testclient import TestClient
from testcontainers.opensearch import OpenSearchContainer
import os


@pytest.fixture(scope="module", autouse=True)
def oss_container():
    os.environ["CONFIG_FILE"] = "config/config.yaml"
    os.environ["DEPLOYMENT_ENVIRONMENT"] = "test"
    with OpenSearchContainer(security_enabled=True) as opensearch:
        yield opensearch


@pytest.fixture(scope="module", autouse=True)
def oss_index(oss_container: OpenSearchContainer):
    config = oss_container.get_config()
    os.environ["OPENSEARCH_HOST"] = config["host"]
    os.environ["OPENSEARCH_PORT"] = config["port"]
    os.environ["OPENSEARCH_USER"] = config["username"]
    os.environ["OPENSEARCH_PASS"] = config["password"]
    index = "test"
    os.environ["OPENSEARCH_INDEX"] = index
    return index


@pytest.fixture(scope="module", autouse=True)
def oss_client(oss_container: OpenSearchContainer, oss_index: str):
    client = oss_container.get_client()
    client.indices.create(index=oss_index)
    return client


@pytest.fixture(autouse=True)
def replace_oss_accessor(oss_client: OpenSearch, oss_index: str):
    from src.main import app, get_oss_accessor

    def get_test_oss_accessor():
        return OssAccessor(oss_index, oss_client)

    app.dependency_overrides[get_oss_accessor] = get_test_oss_accessor
    yield
    app.dependency_overrides.pop(get_oss_accessor)


@pytest.fixture(autouse=True)
def reset_index(oss_client: OpenSearch, oss_index: str):
    oss_client.indices.delete(index=oss_index)
    oss_client.indices.create(index=oss_index)


@pytest.fixture
def test_client(oss_client: OpenSearch):
    from src.main import app

    return TestClient(app)


def test_health_check(test_client: TestClient):
    response = test_client.get("/health-check")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


def test_create_single_document__valid_request(test_client: TestClient):
    response = test_client.post("/documents/test", json={"id": "test", "text": "test"})
    assert response.status_code == 200

    response = test_client.get("/document/test")
    assert response.status_code == 200
    assert response.json()["hits"]["hits"][0]["_source"] == {
        "id": "test",
        "text": "test",
    }


def test_create_single_document__malformed_request(test_client: TestClient):
    response = test_client.post("/documents/test", json={"text": "test"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "input": {"text": "test"},
                "loc": ["body", "id"],
                "msg": "Field required",
                "type": "missing",
            }
        ]
    }


def test_create_multiple_documents__valid_request(test_client: TestClient):
    response = test_client.post(
        "/documents",
        json={"test1": {"id": "test1"}, "test2": {"id": "test2"}},
    )
    assert response.status_code == 200
    assert response.json() is None

    sleep(1)  # wait for data to be available
    response = test_client.get("/document/test1")
    assert response.status_code == 200
    assert response.json()["hits"]["hits"][0]["_source"] == {"id": "test1"}

    response = test_client.get("/document/test2")
    assert response.status_code == 200
    assert response.json()["hits"]["hits"][0]["_source"] == {"id": "test2"}


def test_create_multiple_documents__malformed_request(test_client):
    response = test_client.post("/documents", json={"id": "test"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "input": "test",
                "loc": ["body", "id"],
                "msg": "Input should be a valid dictionary or object to extract fields from",
                "type": "model_attributes_type",
            }
        ]
    }


def test_delete_document__valid_request(
    test_client: TestClient, oss_client: OpenSearch, oss_index: str
):
    oss_client.index(oss_index, {"id": "to_be_deleted"})

    response = test_client.delete("/documents/to_be_deleted")
    assert response.status_code == 200

    response = test_client.get("/document/to_be_deleted")
    assert response.status_code == 200
    assert response.json()["hits"]["total"]["value"] == 0


def test_get_document__valid_request_with_no_fields(
    test_client: TestClient, oss_client: OpenSearch, oss_index: str
):
    document = {"id": "test", "test_field": "test_value"}
    oss_client.index(oss_index, document, "test", params={"refresh": "true"})

    response = test_client.get("/document/test")
    assert response.status_code == 200
    print(response.json())
    assert response.json()["hits"]["hits"][0]["_source"] == document


def test_get_document__valid_request_with_fields(
    test_client: TestClient, oss_client: OpenSearch, oss_index: str
):
    oss_client.index(
        oss_index,
        {"id": "test", "test_field": "test_value", "embedTextHash": "hash"},
        "test",
        params={"refresh": "true"},
    )

    response = test_client.get("/document/test?fields=embedTextHash%2Cid")
    assert response.status_code == 200
    print(response.json())
    assert response.json()["hits"]["hits"][0]["_source"] == {
        "id": "test",
        "embedTextHash": "hash",
    }


def test_documents_no_embedding__valid_request(test_client, mock_oss):
    response = test_client.post(
        "query",
        json={
            "_source": {"includes": ["id"]},
            "query": {"bool": {"must_not": [{"exists": {"field": "test"}}]}},
        },
    )
    assert response.status_code == 200
    assert mock_oss.search.call_count == 1
    assert mock_oss.search.call_args[1] == {
        "index": "test",
        "body": {
            "_source": {"includes": ["id"]},
            "query": {"bool": {"must_not": [{"exists": {"field": "test"}}]}},
        },
    }
    assert response.json() == {
        "took": 1,
        "timed_out": False,
        "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
        "hits": {
            "total": {"value": 1, "relation": "eq"},
            "max_score": 1,
            "hits": [
                {
                    "_index": "test",
                    "_id": "no_embedding",
                    "_score": 0,
                    "_source": {
                        "id": "no_embedding",
                        "test_field": "test_value",
                    },
                }
            ],
        },
    }


def test_documents_no_embedding__invalid_request(test_client, mock_oss):
    response = test_client.post(
        "query",
        json={
            "_source": {"includes": ["id"]},
            "query": {"bool": {"must_not": [{"exists": {"field": ["test"]}}]}},
        },
    )
    assert response.status_code == 400
    assert mock_oss.search.call_count == 1
    assert mock_oss.search.call_args[1] == {
        "index": "test",
        "body": {
            "_source": {"includes": ["id"]},
            "query": {"bool": {"must_not": [{"exists": {"field": ["test"]}}]}},
        },
    }
    assert response.json() == {"detail": "Invalid query: test"}
