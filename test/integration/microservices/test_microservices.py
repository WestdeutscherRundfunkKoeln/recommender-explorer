from datetime import datetime, timedelta, timezone
import time
from pathlib import Path

import httpx
import pytest
from envyaml import EnvYAML
from opensearchpy import OpenSearch, RequestsHttpConnection


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


@pytest.fixture(autouse=True)
def reset_opensearch():
    with OpenSearch(
        hosts=[{"host": "0.0.0.0", "port": 9200}],
        http_auth=("admin", "admin"),
        use_ssl=False,
        verify_certs=False,
        connection_class=RequestsHttpConnection,
        timeout=600,
    ) as client:
        client.indices.create(index="test_index")
        yield
        client.indices.delete(index="test_index")


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
    time.sleep(61)

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
    assert task["completed_items"] == 2
    assert task["failed_items"] == 0
    assert datetime.fromisoformat(task["created_at"]) > start_ts
    assert datetime.fromisoformat(task["completed_at"]) < start_ts + timedelta(
        minutes=1
    )

    # wait for maintainance to run
    time.sleep(61)

    # check documents in opensearch
    ids = [f.removesuffix(".json") for f in files]
    for id in ids:
        resp = search_service.get(f"/documents/{id}")
        assert_document_is_in_opensearch(resp, id)


def test_reembedding_maintenance(search_service: httpx.Client, files: list[str]):
    id = files[0].removesuffix(".json")
    resp = search_service.post(f"/documents/{id}", json={"embedText": "test"})
    assert resp.is_success

    resp = search_service.get(f"/documents/{id}")
    assert resp.is_success

    # wait for maintainance to run
    time.sleep(61)
    resp = search_service.get(f"/documents/{id}")
    assert_document_is_in_opensearch(resp, id)


def test_delta_load_maintenance(
    search_service: httpx.Client, ingest_service: httpx.Client, files: list[str]
):
    ids = [f.removesuffix(".json") for f in files]
    search_service.post(f"/documents/{ids[0]}", json={"test": "test"})

    # poll task status
    resp = ingest_service.get("/tasks")
    assert resp.is_success
    delta_task = sorted(
        [task["id"] for task in resp.json()["tasks"] if task["id"].startswith("delta")]
    )[-1]
    for _ in range(6):
        time.sleep(10)
        resp = ingest_service.get(f"/tasks/{delta_task}")
        task = resp.json()["task"]
        if task["status"] == "COMPLETED":
            break

    task = ingest_service.get(f"/tasks/{delta_task}").json()["task"]
    assert task["status"] == "COMPLETED"
    assert task["errors"] == []
    assert task["completed_items"] == 1
    assert task["failed_items"] == 0

    resp = search_service.get(f"/documents/{ids[0]}")
    assert resp.is_success
    payload = resp.json()
    assert payload["_id"] == ids[0]
    assert list(payload["_source"].keys()) == ["test"]

    time.sleep(90)
    assert_document_is_in_opensearch(search_service.get(f"/documents/{ids[1]}"), ids[1])


def test_delete_maintenance(search_service: httpx.Client, files: list[str]):
    search_service.post("/documents/test", json={"test": "test"})
    assert search_service.get("/documents/test").is_success

    # wait for maintainance tasks to run
    time.sleep(61)

    response = search_service.get("/documents/test")
    assert response.is_error
    assert response.status_code == 404
