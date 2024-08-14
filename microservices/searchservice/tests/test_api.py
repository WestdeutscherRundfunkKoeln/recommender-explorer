import pytest
from opensearchpy import OpenSearch
from src.oss_accessor import OssAccessor
from fastapi.testclient import TestClient


@pytest.fixture
def get_app(monkeypatch):
    monkeypatch.setenv("CONFIG_FILE", "tests/config.yaml")
    from src.main import app

    return app


@pytest.fixture
def test_client(get_app):
    return TestClient(get_app)


@pytest.fixture
def mock_oss(mocker):
    oss = mocker.Mock(spec=OpenSearch)

    def _update(*a, **kw):
        return {
            "_index": kw["index"],
            "_id": kw["id"],
            "_version": 3,
            "result": "updated",
            "_shards": {"total": 2, "successful": 2, "failed": 0},
            "_seq_no": 4,
            "_primary_term": 17,
        }

    oss.update.side_effect = _update

    def _delete(*a, **kw):
        return {
            "_index": kw["index"],
            "_id": kw["id"],
            "_version": 2,
            "result": "deleted",
            "_shards": {"total": 2, "successful": 2, "failed": 0},
            "_seq_no": 1,
            "_primary_term": 15,
        }

    oss.delete.side_effect = _delete
    oss.bulk.return_value = {
        "took": 11,
        "errors": True,
        "items": [
            {
                "index": {
                    "_index": "test",
                    "_id": "test1",
                    "_version": 1,
                    "result": "created",
                    "_shards": {"total": 2, "successful": 1, "failed": 0},
                    "_seq_no": 1,
                    "_primary_term": 1,
                    "status": 201,
                }
            },
            {
                "index": {
                    "_index": "test",
                    "_id": "test2",
                    "_version": 1,
                    "result": "created",
                    "_shards": {"total": 2, "successful": 1, "failed": 0},
                    "_seq_no": 1,
                    "_primary_term": 1,
                    "status": 201,
                }
            },
        ],
    }

    def _search(*a, **kw):
        data = {
            "id": kw["body"]["query"]["ids"]["values"][0],
            "embedTextHash": "IAmAHash",
            "test_field": "test_value",
        }

        if kw["body"]["_source"]["includes"]:
            data = {
                k: v for k, v in data.items() if k in kw["body"]["_source"]["includes"]
            }

        return {
            "took": 1,
            "timed_out": False,
            "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
            "hits": {
                "total": {"value": 1, "relation": "eq"},
                "max_score": 1,
                "hits": [
                    {
                        "_index": kw["index"],
                        "_id": kw["body"]["query"]["ids"]["values"][0],
                        "_score": 1,
                        "_source": data,
                    }
                ],
            },
        }

    oss.search.side_effect = _search

    import json

    transport = mocker.Mock()
    transport.serializer = json
    oss.transport = transport
    yield oss


@pytest.fixture
def mock_oss_accessor(mock_oss):
    return OssAccessor("test", mock_oss)


@pytest.fixture(autouse=True)
def replace_oss_accessor(get_app, mock_oss_accessor):
    from src.main import get_oss_accessor

    get_app.dependency_overrides[get_oss_accessor] = lambda: mock_oss_accessor
    yield
    get_app.dependency_overrides.pop(get_oss_accessor)


def test_health_check(test_client):
    response = test_client.get("/health-check")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


def test_create_single_document__valid_request(test_client, mock_oss):
    response = test_client.post(
        "/create-single-document", json={"id": "test", "text": "test"}
    )
    assert response.status_code == 200

    assert mock_oss.update.call_count == 1
    assert mock_oss.update.call_args[1] == {
        "index": "test",
        "body": {"doc": {"id": "test", "text": "test"}, "doc_as_upsert": True},
        "id": "test",
        "refresh": True,
    }

    assert response.json() == {
        "_index": "test",
        "_id": "test",
        "_version": 3,
        "result": "updated",
        "_shards": {"total": 2, "successful": 2, "failed": 0},
        "_seq_no": 4,
        "_primary_term": 17,
    }


def test_create_single_document__malformed_request(test_client):
    response = test_client.post("/create-single-document", json={"text": "test"})
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


def test_create_multiple_documents__valid_request(test_client, mock_oss, mocker):
    response = test_client.post(
        "/create-multiple-documents",
        json={"test1": {"id": "test1"}, "test2": {"id": "test2"}},
    )
    assert response.status_code == 200

    assert mock_oss.bulk.call_count == 1
    assert mock_oss.bulk.call_args == mocker.call(
        '{"update": {"_id": "test1", "_index": "test"}}\n{"doc": {"id": "test1"}, "doc_as_upsert": true}\n{"update": {"_id": "test2", "_index": "test"}}\n{"doc": {"id": "test2"}, "doc_as_upsert": true}\n',
        index="test",
    )
    assert response.json() is None


def test_create_multiple_documents__malformed_request(test_client):
    response = test_client.post("/create-multiple-documents", json={"id": "test"})
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


def test_delete_document__valid_request(test_client, mock_oss):
    response = test_client.delete("/delete-data", params={"document_id": "test"})
    assert response.status_code == 200

    assert mock_oss.delete.call_count == 1
    assert mock_oss.delete.call_args[1] == {
        "index": "test",
        "id": "test",
    }

    assert response.json() == {
        "_index": "test",
        "_id": "test",
        "_version": 2,
        "result": "deleted",
        "_shards": {"total": 2, "successful": 2, "failed": 0},
        "_seq_no": 1,
        "_primary_term": 15,
    }


def test_delete_document__malformed_request(test_client):
    response = test_client.delete("/delete-data", params={"id": "test"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "input": None,
                "loc": ["query", "document_id"],
                "msg": "Field required",
                "type": "missing",
            }
        ]
    }


def test_get_document__valid_request_with_no_fields(test_client, mock_oss):
    response = test_client.get("/document/test")
    assert response.status_code == 200
    assert mock_oss.search.call_count == 1
    assert mock_oss.search.call_args[1] == {
        "index": "test",
        "body": {"query": {"ids": {"values": ["test"]}}, "_source": {"includes": []}},
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
                    "_id": "test",
                    "_score": 1,
                    "_source": {
                        "id": "test",
                        "embedTextHash": "IAmAHash",
                        "test_field": "test_value",
                    },
                }
            ],
        },
    }


def test_get_document__valid_request_with_fields(test_client, mock_oss):
    response = test_client.get("/document/test?fields=embedTextHash%2Cid")
    assert response.status_code == 200
    assert mock_oss.search.call_count == 1
    assert mock_oss.search.call_args[1] == {
        "index": "test",
        "body": {
            "query": {"ids": {"values": ["test"]}},
            "_source": {"includes": ["embedTextHash", "id"]},
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
                    "_id": "test",
                    "_score": 1,
                    "_source": {
                        "id": "test",
                        "embedTextHash": "IAmAHash",
                    },
                }
            ],
        },
    }
