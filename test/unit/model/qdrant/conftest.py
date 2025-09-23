import pytest
import farmhash
from testcontainers.qdrant import QdrantContainer

from qdrant_client import QdrantClient

COLLECTION_NAME = "test_collection"


@pytest.fixture(autouse=True, scope="session")
def qdrant_container():
    with QdrantContainer("qdrant/qdrant:latest") as qdrant:
        yield qdrant


@pytest.fixture(autouse=True, scope="session")
def qdrant_client(qdrant_container: QdrantContainer):
    return qdrant_container.get_client()


@pytest.fixture(autouse=True)
def setup_qdrant_collection(qdrant_client: QdrantClient):
    collection_name = COLLECTION_NAME
    if not qdrant_client.collection_exists(collection_name):
        qdrant_client.create_collection(
            collection_name, vectors_config={"size": 4, "distance": "Cosine"}
        )
    points = [
        {
            "id": farmhash.fingerprint64("test1"),
            "vector": [0.1, 0.2, 0.3, 0.4],
            "payload": {
                "content_id": "test1",
                "urn": "urn1",
                "field1": "test1",
                "field2": "test2",
                "field3": "test1",
            },
        },
        {
            "id": farmhash.fingerprint64("test2"),
            "vector": [0.2, 0.3, 0.4, 0.5],
            "payload": {
                "content_id": "test2",
                "urn": "urn2",
                "field1": "test1",
                "field2": "test2",
                "field3": "test2",
            },
        },
        {
            "id": farmhash.fingerprint64("test3"),
            "vector": [0.3, 0.4, 0.5, 0.6],
            "payload": {
                "content_id": "test3",
                "urn": "urn3",
                "field1": "test1",
                "field2": "test2",
                "field3": "test3",
            },
        },
        {
            "id": farmhash.fingerprint64("test4"),
            "vector": [0.4, 0.5, 0.6, 0.7],
            "payload": {"content_id": "test4", "urn": "urn4", "field1": "test1"},
        },
        {
            "id": farmhash.fingerprint64("test5"),
            "vector": [0.5, 0.6, 0.7, 0.8],
            "payload": {"content_id": "test5", "urn": "urn5", "field2": "test2"},
        },
    ]
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
    yield
    qdrant_client.delete_collection(collection_name)
