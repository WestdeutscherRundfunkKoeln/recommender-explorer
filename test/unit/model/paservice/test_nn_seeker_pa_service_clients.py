import pytest
from unittest.mock import MagicMock
from src.model.rest.nn_seeker_paservice_clients import NnSeekerPaServiceClients

TEST_CONFIG = {
    "endpoint": "https://test.io/recos",
    "clients_endpoint": "https://test.io/clients",
    "properties": {
        "auth_header": "test",
        "auth_header_value": "test",
        "param_similarityType": "content",
        "param_abGroup": "B",
    },
}

def test_get_clients():
    client = NnSeekerPaServiceClients(TEST_CONFIG)

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.data = b'{"clients": [{"identifier": "client_1"}, {"identifier": "client_2"}]}'

    # Mock the HTTP request
    client._http.request = MagicMock(return_value=mock_response)

    result = client.get_clients()
    assert result == ["client_1", "client_2"]


def test_get_clients_failure():
    client = NnSeekerPaServiceClients(TEST_CONFIG)

    mock_response = MagicMock()
    mock_response.status = 500
    mock_response.data = b'{"error": "Internal server error"}'

    client._http.request = MagicMock(return_value=mock_response)

    with pytest.raises(ValueError) as exc_info:
        client.get_clients()

    assert "Failed to get clients" in str(exc_info.value)
