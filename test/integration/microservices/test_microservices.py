from datetime import datetime, timedelta, timezone
import time
from pathlib import Path

import httpx
import pytest
from envyaml import EnvYAML


@pytest.fixture(scope="module")
def search_service():
    with httpx.Client(base_url="http://0.0.0.0:1336") as client:
        yield client


@pytest.fixture(scope="module")
def ingest_service():
    with httpx.Client(base_url="http://0.0.0.0:1337") as client:
        yield client


@pytest.fixture(scope="module")
def embedding_service():
    with httpx.Client(base_url="http://0.0.0.0:1338") as client:
        yield client


def models():
    path = (
        Path(__file__).parent.parent.parent.parent
        / "microservices"
        / "embeddingservice"
        / "config"
        / "config.yaml"
    )
    embedding_config = EnvYAML(
        path.as_posix(),
        include_environment=False,
        strict=False,
    )
    return [list(model.keys())[0] for model in embedding_config["models"]]


@pytest.fixture(scope="module")
def files():
    dir = Path(__file__).parent.parent.parent / "testdata" / "test"
    return [file.name for file in dir.glob("*.json")]


def assert_document_is_in_opensearch(resp: httpx.Response, id: str) -> None:
    assert resp.is_success
    payload = resp.json()
    assert payload["_id"] == id
    assert "embedTextHash" in payload["_source"]
    for model in models():
        assert model in payload["_source"]


def test_health_check(
    search_service: httpx.Client,
    ingest_service: httpx.Client,
    embedding_service: httpx.Client,
):
    assert search_service.get("/health-check").is_success
    assert ingest_service.get("/health-check").is_success
    assert embedding_service.get("/health-check").is_success


def test_events(
    search_service: httpx.Client,
    ingest_service: httpx.Client,
    files: list[str],
):
    file = files[0]
    id = files[0].removesuffix(".json")

    # A creation event comes in
    resp = ingest_service.post(
        "/events",
        json={"bucket": "test", "name": file},
        headers={"eventType": "OBJECT_FINALIZE"},
    )
    assert resp.is_success
    assert resp.json()["_id"] == id

    # wait until sync is done
    time.sleep(15)

    # The document is available in the opensearch with embeddings
    resp = search_service.get(f"/documents/{id}")
    assert_document_is_in_opensearch(resp, id)

    # A deletion event comes in
    resp = ingest_service.post(
        "/events",
        json={"bucket": "test", "name": file},
        headers={"eventType": "OBJECT_DELETE"},
    )
    assert resp.is_success
    assert resp.json()["_id"] == id

    # The document is available in the opensearch with embeddings
    resp = search_service.get(f"/documents/{id}")
    assert resp.status_code == 404


def test_bulk_ingest(
    search_service: httpx.Client,
    ingest_service: httpx.Client,
    files: list[str],
):
    start_ts = datetime.now(tz=timezone.utc)

    # trigger full ingest
    resp = ingest_service.post(
        "/ingest-multiple-items",
        json={"bucket": "test", "prefix": ""},
    )
    assert resp.is_success
    task_id = resp.json()["task_id"]

    # check task status
    resp = ingest_service.get(f"/tasks/{task_id}")
    assert resp.is_success
    task = resp.json()["task"]
    assert task["id"] == task_id
    assert task["status"] == "PREPROCESSING"
    assert task["errors"] == []
    assert datetime.fromisoformat(task["created_at"]) > start_ts
    assert task["completed_at"] is None

    # poll task status
    for _ in range(6):
        time.sleep(10)
        resp = ingest_service.get(f"/tasks/{task_id}")
        task = resp.json()["task"]
        if task["status"] == "COMPLETED":
            break

    # check final task status
    assert task["id"] == task_id
    assert task["status"] == "COMPLETED"
    assert task["errors"] == []
    assert datetime.fromisoformat(task["created_at"]) > start_ts
    assert datetime.fromisoformat(task["completed_at"]) < start_ts + timedelta(
        minutes=1
    )

    # wait for maintainance to run
    time.sleep(11)

    # check documents in opensearch
    ids = [f.removesuffix(".json") for f in files]
    for id in ids:
        resp = search_service.get(f"/documents/{id}")
        assert_document_is_in_opensearch(resp, id)


def test_reembedding_maintenance(search_service: httpx.Client):
    id = "no_embedding"
    resp = search_service.post("/documents/no_embedding", json={"embedText": "test"})
    assert resp.is_success

    resp = search_service.get("/documents/no_embedding")
    assert resp.is_success

    # wait for maintainance to run
    time.sleep(11)
    resp = search_service.get("/documents/no_embedding")
    assert_document_is_in_opensearch(resp, id)
