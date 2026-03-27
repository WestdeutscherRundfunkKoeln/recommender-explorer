import pytest
from qdrant_client import QdrantClient

from src.dto.content_item import ContentItemDto
from src.model.qdrant.nn_seeker_qdrant import QdrantNNSeeker

from test.unit.model.qdrant.conftest import COLLECTION_NAME


def test_qdrant_nn_seeker_get_k_NN(qdrant_client: QdrantClient):
    item = ContentItemDto(
        id="test1", _position="start", _item_type="content", _provenance="test"
    )

    nn_seeker = QdrantNNSeeker(qdrant_client)
    nn_seeker.set_model_config({"endpoint": f"qdrant://{COLLECTION_NAME}"})
    ids, scores, id_field = nn_seeker.get_k_NN(
        item=item, k=2, nn_filter={"field1": "test1", "field2": "test2"}
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
            item=item, k=2, nn_filter={"field1": "test1", "field2": "test2"}
        )
