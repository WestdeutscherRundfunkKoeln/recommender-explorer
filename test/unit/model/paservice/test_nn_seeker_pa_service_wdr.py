import json

from urllib3 import HTTPResponse

from src.dto.content_item import ContentItemDto
from src.model.rest.nn_seeker_paservice_wdr import NnSeekerPaServiceWDR

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
    "display_name": "PA-Service - WDR",
    "handler": "NnSeekerPaServiceWDR@model.rest.nn_seeker_paservice_wdr",
    "endpoint": "https://test.io/recos",
    "content_type": "WDRContentItemDto",
    "properties": {
        "auth_header": "test",
        "auth_header_value": "test",
        "param_similarityType": "content",
        "param_abGroup": "B",
    },
    "default": False,
}


def test_get_k_NN(mocker):
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
    nn_seeker = NnSeekerPaServiceWDR(TEST_CONFIG)
    nn_seeker.set_model_config(TEST_MODEL_CONFIG_C2C)
    ids, scores, oss_field = nn_seeker.get_k_NN(
        ContentItemDto("test", "test", "test", externalid="test"), 3, {}
    )
    assert ids == ["test2", "test1"]
    assert scores == [0.2, 0.1]
    assert oss_field == "externalid"
    mock_request.assert_called_once_with(
        "POST",
        "https://test.io/recos",
        fields={
            "referenceId": "test",
            "excludedIds": ["test1", "test2"],
            "maxDurationFactor": 1.0,
            "reco": False,
            "weights": [
                {
                    "type": "w1",
                    "weight": 1,
                },
                {
                    "type": "w2",
                    "weight": 2,
                },
            ],
        },
        headers={"test": "test"},
    )
