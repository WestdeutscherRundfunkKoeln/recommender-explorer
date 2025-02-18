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
    "endpoint": "https://test.io/recos",
    "properties": {
        "auth_header": "test",
        "auth_header_value": "test",
    },
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
        item=ContentItemDto("test", "test", "test", externalid="test"),
        k=3,
        nn_filter={
            "relativerangefilter_duration": 100,
            "blacklist_externalid": "test_blacklist_id1,test_blacklist_id2",
            "weight_audio": 1,
            "weight_video": 2,
        },
    )
    assert ids == ["test2", "test1"]
    assert scores == [0.2, 0.1]
    assert oss_field == "externalid"
    mock_request.assert_called_once_with(
        "POST",
        "https://test.io/recos",
        fields={
            "referenceId": "test",
            "excludedIds": ["test_blacklist_id1", "test_blacklist_id2"],
            "maxDurationFactor": 100,
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
