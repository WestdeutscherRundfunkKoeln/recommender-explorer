import json
import pytest

from urllib3 import HTTPResponse

from src.dto.content_item import ContentItemDto
from src.model.rest.nn_seeker_paservice_news import NnSeekerPaServiceNews
from src.exceptions.item_not_found_error import UnknownItemError

TEST_CONFIG = {
    "opensearch": {
        "field_mapping": {
            "created": "availableFrom",
            "createdFormatted": "availableFrom",
            "showTitle": "showTitel",
            "crid": "externalid",
            "duration": "duration",
        },
        "primary_field": "crid",
    }
}

TEST_MODEL_CONFIG_C2C = {
    "endpoint": "https://test.io/recos",
    "properties": {
        "auth_header": "test",
        "auth_header_value": "test",
    },
}


def test_get_k_NN_WDR(mocker):
    mock_request = mocker.patch(
        "urllib3.PoolManager.request",
        return_value=HTTPResponse(
            body=json.dumps(
                {
                    "items": [
                        {"score": 0.2, "id": "test2"},
                        {"score": 0.1, "id": "test1"},
                    ]
                }
            ).encode(),
            status=200,
        ),
    )
    nn_seeker = NnSeekerPaServiceNews(TEST_CONFIG)
    nn_seeker.set_model_config(TEST_MODEL_CONFIG_C2C)
    ids, scores, oss_field, utilities = nn_seeker.get_k_NN(
        item=ContentItemDto("test", "test", "test", externalid="test"),
        k=3,
        nn_filter={
            "utilities": [
                {
                    "utility": "semanticWeight",
                    "weight": 0.35
                },
                {
                    "utility": "timeWeight",
                    "weight": 0.2
                }
            ],
            "filter": {
                "maxDurationFactor_duration": 25.75,
                "excludedIds": "test_blacklist_id1,test_blacklist_id2"
            },
            "weights": [
                {
                    "type": "audio",
                    "weight": 1,
                },
                {
                    "type": "video",
                    "weight": 2,
                },
            ],
        }
    )



    assert ids == ["test2", "test1"]
    assert scores == [0.2, 0.1]
    assert oss_field == "externalid"
    mock_request.assert_called_once_with(
        "POST",
        "https://test.io/recos",
        json={
            "filter": {
                "maxDurationFactor_duration": 25.75,
                "excludedIds": "test_blacklist_id1,test_blacklist_id2"
            },
            "utilities": [
                {
                    "utility": "semanticWeight",
                    "weight": 0.35
                },
                {
                    "utility": "timeWeight",
                    "weight": 0.2
                }
            ],
            "referenceId": "test",
            "reco": False,
            "weights": [
                {
                    "type": "audio",
                    "weight": 1,
                },
                {
                    "type": "video",
                    "weight": 2,
                },
            ],
        },
        headers={"test": "test"},
    )


def test_get_k_NN_exception(mocker):
    mock_request = mocker.patch(
        "urllib3.PoolManager.request",
        return_value=HTTPResponse(
            body=json.dumps({"error": "not found"}).encode(),
            status=404,
        ),
    )
    nn_seeker = NnSeekerPaServiceNews(TEST_CONFIG)
    nn_seeker.set_model_config(TEST_MODEL_CONFIG_C2C)
    with pytest.raises(Exception):
        _ = nn_seeker.get_k_NN(
            item=ContentItemDto("test", "test", "test", externalid="test"),
            k=3,
            nn_filter={
                "utilities": [
                    {
                        "utility": "semanticWeight",
                        "weight": 0.35
                    },
                    {
                        "utility": "timeWeight",
                        "weight": 0.2
                    }
                ],
                "filter": {
                    "maxDurationFactor_duration": 25.75,
                    "excludedIds": "test_blacklist_id1,test_blacklist_id2"
                },
                "weights": [
                    {
                        "type": "audio",
                        "weight": 1,
                    },
                    {
                        "type": "video",
                        "weight": 2,
                    },
                ],
            },
        )
    mock_request.assert_called_once_with(
        "POST",
        "https://test.io/recos",
        json={
            "filter": {
                "maxDurationFactor_duration": 25.75,
                "excludedIds": "test_blacklist_id1,test_blacklist_id2"
            },
            "utilities": [
                {
                    "utility": "semanticWeight",
                    "weight": 0.35
                },
                {
                    "utility": "timeWeight",
                    "weight": 0.2
                }
            ],
            "referenceId": "test",
            "reco": False,
            "weights": [
                {
                    "type": "audio",
                    "weight": 1,
                },
                {
                    "type": "video",
                    "weight": 2,
                },
            ],
        },
        headers={"test": "test"},
    )


def test_get_k_NN_BR(mocker):
    mock_request = mocker.patch(
        "urllib3.PoolManager.request",
        return_value=HTTPResponse(
            body=json.dumps(
                {
                    "items": [
                        {"score": 0.2, "id": "test2"},
                        {"score": 0.1, "id": "test1"},
                    ]
                }
            ).encode(),
            status=200,
        ),
    )
    nn_seeker = NnSeekerPaServiceNews(TEST_CONFIG)
    nn_seeker.set_model_config(TEST_MODEL_CONFIG_C2C)
    ids, scores, oss_field, utilities = nn_seeker.get_k_NN(
        item=ContentItemDto("test", "test", "test", externalid="test"),
        k=3,
        nn_filter={
            "refinement": {
                "direction": "more similar",
                "previousExternalIds": [
                    "test2",
                    "test1"
                ]
            },
            "utilities": [
                {
                    "utility": "semanticWeight",
                    "weight": 0.35
                },
                {
                    "utility": "tagWeight",
                    "weight": 0.35
                },
                {
                    "utility": "timeWeight",
                    "weight": 0.2
                },
                {
                    "utility": "localTrendWeight",
                    "weight": 0.1
                }
            ],
        },
    )
    assert ids == ["test2", "test1"]
    assert scores == [0.2, 0.1]
    assert oss_field == "externalid"
    mock_request.assert_called_once_with(
        "POST",
        "https://test.io/recos",
        json={
            "refinement": {
                "direction": "more similar",
                "previousExternalIds": [
                    "test2",
                    "test1",
                ]
            },
            "utilities": [
                {
                    "utility": "semanticWeight",
                    "weight": 0.35
                },
                {
                    "utility": "tagWeight",
                    "weight": 0.35
                },
                {
                    "utility": "timeWeight",
                    "weight": 0.2
                },
                {
                    "utility": "localTrendWeight",
                    "weight": 0.1
                }
            ],
            "referenceId": "test",
            "reco": False
    },
        headers={"test": "test"},
    )
