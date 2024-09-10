import json

import pytest
from pytest_httpx import HTTPXMock
from src.dto.pa_service_content_item import PaServiceContentItemDto
from src.model.paservice.base_data_accessor_pa_service import BaseDataAccessorPaService


def test_get_item_by_external_id__valid_request(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        status_code=200,
        json={
            "items": [
                {"id": "test", "score": 1.0, "item": {}},
                {"id": "test_1", "score": 0.1, "item": {}},
                {"id": "test_2", "score": 0.2, "item": {}},
            ]
        },
    )
    pa_service = BaseDataAccessorPaService(
        {
            "pa_service": {
                "host": "https://test.io",
                "auth_header": "test",
                "auth_header_value": "test",
                "endpoint": "wdrRecommendation",
                "field_mapping": {"external_id": "id"},
            }
        }
    )

    res = pa_service.get_item_by_external_id(
        PaServiceContentItemDto("0", "start", ""),
        "test",
        filter={
            "relativerangefilter_duration": 100,
            "blacklist_externalid": "test_blacklist_id",
            "weight_audio": 5,
            "weight_video": 5,
        },
    )

    assert res == (
        [
            PaServiceContentItemDto("start", "start", "", score=1.0),
            PaServiceContentItemDto("reco", "start", "", score=0.1),
            PaServiceContentItemDto("reco", "start", "", score=0.2),
        ],
        3,
    )
    assert httpx_mock.get_requests()[0].url == "https://test.io/wdrRecommendation"
    assert (
        httpx_mock.get_requests()[0].content
        == json.dumps(
            {
                "referenceId": "test",
                "reco": "true",
                "maxDurationFactor": 100,
                "excludedIds": ["test_blacklist_id"],
                "weights": [
                    {"type": "audio", "weight": 5},
                    {"type": "video", "weight": 5},
                ],
            }
        ).encode()
    )


def test_get_item_by_external_id__incorrect_weighting(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=400)
    pa_service = BaseDataAccessorPaService(
        {
            "pa_service": {
                "host": "https://test.io",
                "auth_header": "test",
                "auth_header_value": "test",
                "endpoint": "wdrRecommendation",
                "field_mapping": {"external_id": "id"},
            }
        }
    )

    with pytest.raises(Exception):
        pa_service.get_item_by_external_id(
            PaServiceContentItemDto("0", "start", ""),
            "test",
            filter={
                "relativerangefilter_duration": 100,
                "blacklist_externalid": "test_blacklist_id",
                "weight_video": 5,
            },
        )
