import json
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


@pytest.fixture(scope="module")
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


def _get_sophora_id(file: Path) -> str:
    with file.open() as f:
        return json.load(f)["sophoraId"]


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
    models: list[str],
    files: list[str],
):
    file = files[0]
    id = files[0].split(".")[0]

    # A creation event comes in
    resp = ingest_service.post(
        "/events",
        json={"bucket": "test", "name": file},
        headers={"eventType": "OBJECT_FINALIZE"},
    )
    assert resp.is_success
    assert resp.json()["_id"] == id

    # wait until sync is done
    time.sleep(1)

    # The document is available in the opensearch with embeddings
    resp = search_service.get(f"/document/{id}")
    assert resp.is_success
    payload = resp.json()
    print(list(payload["_source"].keys()))
    assert payload["_id"] == id
    assert "embedTextHash" in payload["_source"]
    for model in models:
        assert model in payload["_source"]

    # A deletion event comes in
    resp = ingest_service.post(
        "/events",
        json={"bucket": "test", "name": file},
        headers={"eventType": "OBJECT_DELETE"},
    )
    assert resp.is_success
    assert resp.json()["_id"] == id

    # The document is available in the opensearch with embeddings
    resp = search_service.get(f"/document/{id}")
    assert resp.status_code == 404
