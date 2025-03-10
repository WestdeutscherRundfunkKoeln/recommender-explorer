import pytest
from pathlib import Path
import os
import yaml

from src.util.file_utils import (
    get_client_options,
    get_configs_from_arg,
    load_ui_config,
    get_client_ident_from_search,
    _get_model_config_from_endpoint,
    load_model_configuration,
    ConfigError
)

TEST_CONFIGS_DIRECTORY = "test_configs"

def load_yaml_config(filename):
    file_path = os.path.join(os.path.dirname(__file__), TEST_CONFIGS_DIRECTORY, filename)
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


@pytest.fixture
def config_dummy():
    return Path(__file__).parent / TEST_CONFIGS_DIRECTORY / "config_dummy.yaml"


@pytest.fixture
def config_test():
    return Path(__file__).parent / TEST_CONFIGS_DIRECTORY / "config_test.yaml"


@pytest.fixture
def full_path():
    return Path(__file__).parent / "test_config.yaml"


@pytest.fixture
def config_with_model_key():
    return load_yaml_config("config_with_model_key.yaml")


@pytest.fixture
def config_without_model_key():
    return load_yaml_config("config_without_model_key.yaml")


@pytest.fixture
def config_missing_required_keys():
    return load_yaml_config("config_missing_required_keys.yaml")


@pytest.fixture
def local_config_with_c2c():
    return load_yaml_config("local_config_with_c2c.yaml")


@pytest.fixture
def local_config_with_u2c():
    return load_yaml_config("local_config_with_u2c.yaml")


def test_load_ui_config__valid_config(full_path):
    config = {
        "test": "test",
        "ui_config": Path(__file__).parent / TEST_CONFIGS_DIRECTORY / "test_ui_config.yaml",
    }

    result = load_ui_config(config, full_path)

    assert result == {
        "test": "test",
        "ui_config": {"title": "Test Recommender Explorer"},
        "ui_config.title": "Test Recommender Explorer",
    }


def test_load_ui_config__no_config(full_path):
    config = {"test": "test"}

    result = load_ui_config(config, full_path)

    assert result == config


def test_load_ui_config__wrong_config(full_path):
    config = {
        "test": "test",
        "ui_config": Path(__file__).parent / "this_config_does_not_exist.yaml",
    }

    result = load_ui_config(config, full_path)

    assert result == config


def test_load_ui_config__inline_config(full_path):
    config = {"test": "test", "ui_config": {"title": "Test Recommender Explorer"}}

    result = load_ui_config(config, full_path)

    assert result == config


def test_get_client_options(config_dummy, config_test):
    result = get_client_options({"test": config_test, "dummy": config_dummy})

    assert result == {"test_entry_from_config_file": "test", "Dummy": "dummy"}


def test_get_configs_from_arg__multiple_configs(config_test, config_dummy):
    args = f"config={config_test},{config_dummy}"

    result = get_configs_from_arg(args)

    assert result == ("test", config_test, {"test": config_test, "dummy": config_dummy})


def test_get_configs_from_arg__invalid_config(config_dummy):
    args = f"config=./nonexistent.yaml,{config_dummy}"

    with pytest.raises(Exception):
        get_configs_from_arg(args)


def test_get_client_ident_from_search():
    assert get_client_ident_from_search("?client=test") == "test"
    assert get_client_ident_from_search("?field=test") is None


def test_get_model_config_from_endpoint_with_model_key(httpx_mock, config_with_model_key):
    httpx_mock.add_response(
        url="https://example.com/model_config/test_key",
        method="GET",
        json={"config": "model_key_data"}
    )

    result = _get_model_config_from_endpoint(config_with_model_key)

    assert result == {"config": "model_key_data"}


def test_get_model_config_from_endpoint_without_model_key(httpx_mock, config_without_model_key):
    httpx_mock.add_response(
        url="https://example.com/model_config",
        method="GET",
        json={"config": "all_models_data"}
    )

    result = _get_model_config_from_endpoint(config_without_model_key)

    assert result == {"config": "all_models_data"}


def test_get_model_config_from_endpoint_missing_required_keys(config_missing_required_keys):
    with pytest.raises(ConfigError, match="Missing base URL or API key in configuration."):
        _get_model_config_from_endpoint(config_missing_required_keys)


def test_load_model_configuration__local_c2c_config(local_config_with_c2c):
    result = load_model_configuration(local_config_with_c2c)

    assert result == {"c2c_config": {"c2c_models": ["model1", "model2"]}}


def test_load_model_configuration__local_u2c_config(local_config_with_u2c):
    result = load_model_configuration(local_config_with_u2c)

    assert result == {"u2c_config": {"u2c_models": ["model3", "model4"]}}


def test_load_model_configuration__fetch_from_endpoint(mocker, config_without_model_key):
    mocked_get_model_config = mocker.patch("src.util.file_utils._get_model_config_from_endpoint")
    mocked_get_model_config.return_value = {
        "c2c_models": ["remote_model1"],
        "u2c_models": ["remote_model2"],
    }

    result = load_model_configuration(config_without_model_key)

    mocked_get_model_config.assert_called_once_with(config_without_model_key)
    assert result == {
        "c2c_config": {"c2c_models": ["remote_model1"]},
        "u2c_config": {"u2c_models": ["remote_model2"]},
    }
