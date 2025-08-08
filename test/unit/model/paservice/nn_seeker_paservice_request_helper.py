import pytest
from unittest.mock import MagicMock
from model.rest.nn_seeker_paservice_request_helper import RequestHelper

TEST_CONFIG = {
    "endpoint": "https://test.io/recos",
    "clients_endpoint": "https://test.io/clients",
    "properties": {
        "auth_header": "x",
        "auth_header_value": "y"
    },
}

def test_set_model_config_success():
    helper = RequestHelper()
    helper.set_model_config(TEST_CONFIG)
    assert helper._endpoint == "https://test.io/recos"
    assert helper._model_props["auth_header"] == "x"

def test_set_model_config_missing_endpoint():
    helper = RequestHelper()
    with pytest.raises(ValueError, match="endpoint.*required"):
        helper.set_model_config({"properties": {"auth_header": "x", "auth_header_value": "y"}})

def test_set_model_config_invalid_props():
    helper = RequestHelper()
    with pytest.raises(ValueError, match="properties.*required"):
        helper.set_model_config({"endpoint": "https://test.io/recos", "properties": None})

def test_get_headers():
    helper = RequestHelper()
    helper.set_model_config(TEST_CONFIG)
    headers = helper.get_headers()
    assert headers == {"x": "y"}

def test_get_success():
    helper = RequestHelper()
    helper.set_model_config(TEST_CONFIG)

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.data = b'{"result": "ok"}'

    helper._http.request = MagicMock(return_value=mock_response)

    status, data = helper.get()
    assert status == 200
    assert data == {"result": "ok"}

def test_post_success():
    helper = RequestHelper()
    helper.set_model_config(TEST_CONFIG)

    mock_response = MagicMock()
    mock_response.status = 201


    helper._http.request = MagicMock(return_value=mock_response)

    status, data = helper.post(json_body={"some": "data"})
    assert status == 201
