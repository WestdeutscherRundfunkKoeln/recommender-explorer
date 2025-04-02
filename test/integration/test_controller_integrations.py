import logging
import time
import httpx

from opensearchpy import OpenSearch

import src.constants as constants
import pytest

from src.controller.reco_controller import RecommendationController
from test.test_util import mock_start_filter_component, mock_reco_filter_component

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def ingest_service():
    with httpx.Client(base_url="http://0.0.0.0:1337") as client:
        yield client


@pytest.fixture(autouse=True, scope="session")
def setup_index(config, ingest_service):
    if config["opensearch.host"] != "0.0.0.0":
        return
    use_ssl = config.get("opensearch.use_ssl", True)
    client = OpenSearch(
        hosts=[
            {
                "host": config["opensearch.host"],
                "port": config["opensearch.port"],
            }
        ],
        http_auth=(config["opensearch.user"], config["opensearch.pass"]),
        use_ssl=use_ssl,
        verify_certs=use_ssl,
    )
    client.indices.create(
        index=config["opensearch.index"],
        body={
            "settings": {"index": {"knn": True}},
            "mappings": {
                "properties": {
                    "jina-embeddings-v2-base-de-8192": {
                        "type": "knn_vector",
                        "dimension": 768,
                        "method": {
                            "name": "hnsw",
                            "engine": "lucene",
                            "parameters": {"ef_construction": 128, "m": 24},
                        },
                    }
                }
            },
        },
    )
    resp = ingest_service.post(
        "/ingest-multiple-items",
        json={"bucket": "test", "prefix": ""},
    )
    assert resp.is_success
    task_id = resp.json()["task_id"]

    # poll task status
    for _ in range(60):
        time.sleep(1)
        resp = ingest_service.get(f"/tasks/{task_id}")
        task = resp.json()["task"]
        if task["status"] == "COMPLETED":
            break


@pytest.mark.parametrize(
    "start_component, model",
    [
        (
            [True, "genre_users", "_check_category", "Comedy"],
            ["PA-Service-Var-I", constants.MODEL_CONFIG_U2C],
        )
    ],
)
def test_get_items_one_u2c_model_succeeds(
    u2c_controller: RecommendationController,
) -> None:
    items = u2c_controller.get_items()
    assert isinstance(items, tuple)
    recos = items[1]
    users = []
    for one_result in recos:
        users.append(one_result[0].id)
    # assert users are correct
    assert len(users) == len(set(users))


@pytest.mark.parametrize(
    "selection_type, start_component, model",
    [
        (
            "_by_date",
            {
                "validator": "_check_date",
                "label": "dateinput",
                "accessor": "get_items_by_date",
                "has_paging": True,
            },
            ["Jina-A", constants.MODEL_CONFIG_C2C],
        )
    ],
)
def test_get_items_one_c2c_model_by_date_succeeds(
    c2c_controller: RecommendationController,
) -> None:
    items = c2c_controller.get_items()
    assert isinstance(items, tuple)


@pytest.mark.parametrize(
    "selection_type, start_component, model",
    [
        (
            "_by_date",
            {
                "validator": "_check_date",
                "label": "dateinput",
                "accessor": "get_items_by_date",
                "has_paging": True,
            },
            ["Jina-A", constants.MODEL_CONFIG_C2C],
        )
    ],
)
def test_get_items_one_c2c_model_by_date_with_thematic_start_filter_succeeds(
    c2c_controller: RecommendationController,
) -> None:
    expected_start_theme = c2c_controller.get_item_defaults("type")[0]
    filter_selection = {
        "label": "type",
        "selected_value": [expected_start_theme],
    }
    mock_filter = mock_start_filter_component(filter_selection)
    c2c_controller.register("item_filter", mock_filter)
    c2c_controller.set_num_items(10)
    response = c2c_controller.get_items()
    assert isinstance(response, tuple)
    _, items, _ = response
    for row in items:
        for item in row:
            if item.position == "reco":
                continue
            assert expected_start_theme in item.type


@pytest.mark.parametrize(
    "selection_type, start_component, model",
    [
        (
            "_by_date",
            {
                "validator": "_check_date",
                "label": "dateinput",
                "accessor": "get_items_by_date",
                "has_paging": True,
            },
            ["Jina-A", constants.MODEL_CONFIG_C2C],
        )
    ],
)
def test_get_items_one_c2c_model_by_date_with_reco_sorting_succeeds(
    c2c_controller: RecommendationController,
) -> None:
    sorting = {"label": "sort_recos", "selected_value": ["desc"]}
    mock_reco_filter = mock_reco_filter_component(sorting)
    c2c_controller.register("reco_filter", mock_reco_filter)
    c2c_controller.set_num_items(10)
    response = c2c_controller.get_items()
    assert isinstance(response, tuple)
