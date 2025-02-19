import json

from urllib3 import HTTPResponse

from src.constants import ITEM_POSITION_START
from src.dto.content_item import ContentItemDto
from src.dto.user_item import UserItemDto
from src.model.opensearch.base_data_accessor_opensearch import (
    BaseDataAccessorOpenSearch,
)
from src.model.rest.nn_seeker_paservice import NnSeekerPaService
from src.model.rest.nn_seeker_paservice_show import NnSeekerPaServiceShow

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
        "param_similarityType": "content",
        "param_abGroup": "B",
    },
}

TEST_MODEL_CONFIG_U2C = {
    "endpoint": "https://test.io/recos",
    "properties": {
        "auth_header": "test",
        "auth_header_value": "test",
        "param_modelType": "collab_matrix_model_episode_var1",
        "param_assetReturnType": "episode",
        "user_type": "UserItemDto",
    },
}


def test_get_k_NN(mocker):
    mock_request = mocker.patch(
        "urllib3.PoolManager.request",
        return_value=HTTPResponse(
            body=json.dumps(
                {
                    "recommendations": [
                        {"score": 0.2, "asset": {"assetId": "test2"}},
                        {"score": 0.1, "asset": {"assetId": "test1"}},
                    ]
                }
            ).encode(),
            status=200,
        ),
    )
    nn_seeker = NnSeekerPaService(TEST_CONFIG)
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
        json={
            "configuration": "relatedItems",
            "assetId": "test",
            "limit": 16,
            "similarityType": "content",
            "abGroup": "B",
        },
        headers={"test": "test"},
    )


def test_get_recos_user(mocker):
    mock_request = mocker.patch(
        "urllib3.PoolManager.request",
        return_value=HTTPResponse(
            body=json.dumps(
                {
                    "recommendations": [
                        {"score": 0.2, "asset": {"assetId": "test2"}},
                        {"score": 0.1, "asset": {"assetId": "test1"}},
                    ]
                }
            ).encode(),
            status=200,
        ),
    )
    nn_seeker = NnSeekerPaService(TEST_CONFIG)
    nn_seeker.set_model_config(TEST_MODEL_CONFIG_U2C)

    ids, scores, oss_field = nn_seeker.get_recos_user(
        UserItemDto(ITEM_POSITION_START, "test", "test", "test"),
        3,
        {"editorialCategories": ["test1", "test2"]},
    )

    assert ids == ["test2", "test1"]
    assert scores == [0.2, 0.1]
    assert oss_field == "externalid"

    mock_request.assert_called_once_with(
        "POST",
        "https://test.io/recos",
        json={
            "configuration": "forYou",
            "explain": True,
            "userId": "test",
            "modelType": "collab_matrix_model_episode_var1",
            "assetReturnType": "episode",
            "includedCategories": "test1,test2",
        },
        headers={"test": "test"},
    )


def test_nn_seeker_pa_service_show_get_recos_user(mocker):
    mock_request = mocker.patch(
        "urllib3.PoolManager.request",
        return_value=HTTPResponse(
            body=json.dumps(
                {
                    "recommendations": [
                        {"score": 0.2, "asset": {"assetId": "test2"}},
                        {"score": 0.1, "asset": {"assetId": "test1"}},
                    ]
                }
            ).encode(),
            status=200,
        ),
    )
    mock_item_accessor = mocker.Mock(spec=BaseDataAccessorOpenSearch)

    def mock_get_item_by_urn(item_dto, show_id):
        item_dto.episode = show_id + "_1"
        return [[item_dto]]

    mock_item_accessor.get_item_by_urn.side_effect = mock_get_item_by_urn
    nn_seeker = NnSeekerPaServiceShow(TEST_CONFIG, mock_item_accessor)
    nn_seeker.set_model_config(TEST_MODEL_CONFIG_U2C)

    ids, scores, oss_field = nn_seeker.get_recos_user(
        UserItemDto(ITEM_POSITION_START, "test", "test", "test"),
        3,
        {"editorialCategories": ["test1", "test2"]},
    )

    assert ids == ["test2_1", "test1_1"]
    assert scores == [0.2, 0.1]
    assert oss_field == "externalid"

    mock_request.assert_called_once_with(
        "POST",
        "https://test.io/recos",
        json={
            "configuration": "forYou",
            "explain": True,
            "userId": "test",
            "modelType": "collab_matrix_model_episode_var1",
            "assetReturnType": "episode",
            "includedCategories": "test1,test2",
        },
        headers={"test": "test"},
    )
