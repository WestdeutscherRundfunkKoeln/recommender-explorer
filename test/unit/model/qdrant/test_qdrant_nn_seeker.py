import farmhash
import pytest
from qdrant_client import QdrantClient
from testcontainers.qdrant import QdrantContainer

from src.dto.content_item import ContentItemDto
from src.model.qdrant.nn_seeker_qdrant import QdrantNNSeeker


@pytest.fixture(autouse=True, scope="module")
def qdrant_container():
    with QdrantContainer("qdrant/qdrant:latest") as qdrant:
        yield qdrant


@pytest.fixture(autouse=True, scope="module")
def qdrant_client(qdrant_container: QdrantContainer):
    return qdrant_container.get_client()


COLLECTION_NAME = "test_collection"


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
            "payload": {"content_id": "test1", "field1": "test", "field2": "test"},
        },
        {
            "id": farmhash.fingerprint64("test2"),
            "vector": [0.2, 0.3, 0.4, 0.5],
            "payload": {"content_id": "test2", "field1": "test", "field2": "test"},
        },
        {
            "id": farmhash.fingerprint64("test3"),
            "vector": [0.3, 0.4, 0.5, 0.6],
            "payload": {"content_id": "test3", "field1": "test", "field2": "test"},
        },
        {
            "id": farmhash.fingerprint64("test4"),
            "vector": [0.4, 0.5, 0.6, 0.7],
            "payload": {"content_id": "test4", "field1": "test"},
        },
        {
            "id": farmhash.fingerprint64("test5"),
            "vector": [0.5, 0.6, 0.7, 0.8],
            "payload": {"content_id": "test5", "field2": "test"},
        },
    ]
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
    yield
    qdrant_client.delete_collection(collection_name)


def test_qdrant_nn_seeker_get_k_NN(qdrant_client: QdrantClient):
    item = ContentItemDto(
        id="test1", _position="start", _item_type="content", _provenance="test"
    )

    nn_seeker = QdrantNNSeeker(qdrant_client)
    nn_seeker.set_model_config({"endpoint": f"qdrant://{COLLECTION_NAME}"})
    ids, scores, id_field = nn_seeker.get_k_NN(
        item=item, k=2, nn_filter={"field1": "test", "field2": "test"}
    )

    assert ids == ["test2", "test3"]
    assert len(scores) == 2
    assert all(0.0 <= score <= 1.0 for score in scores)
    assert id_field == ""


def test_qdrant_nn_seeker_no_collection_set(qdrant_client: QdrantClient):
    item = ContentItemDto(
        id="test1", _position="start", _item_type="content", _provenance="test"
    )

    nn_seeker = QdrantNNSeeker(qdrant_client)
    with pytest.raises(ValueError):
        nn_seeker.get_k_NN(
            item=item, k=2, nn_filter={"field1": "test", "field2": "test"}
        )
