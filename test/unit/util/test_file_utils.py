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

from src.util.dataclasses.setup_configuration_data_class import SetupConfiguration
from src.util.dataclasses.opensearch_configuration_data_class import OpenSearchConfiguration
from src.util.dataclasses.model_configuration_data_class import (
    ModelConfiguration,
    C2CConfig,
    U2CConfig,
    ModelDetails,
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


@pytest.fixture
def local_config_with_clustering_model():
    return load_yaml_config("local_config_with_clustering_model.yaml")


@pytest.fixture
def local_config_with_index():
    return load_yaml_config("local_config_with_index.yaml")

@pytest.fixture
def local_config_without_index():
    return load_yaml_config("local_config_without_index.yaml")


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


def test_load_model_configuration__local_index_config(local_config_with_index):
    result = load_model_configuration(local_config_with_index)

    expected = SetupConfiguration(
        model_config=ModelConfiguration(),
        open_search_config=OpenSearchConfiguration(index="local_index")
    )

    assert result.to_dict() == expected.to_dict()


def test_load_model_configuration__local_c2c_config(local_config_with_c2c):
    result = load_model_configuration(local_config_with_c2c)

    expected = SetupConfiguration(
        model_config=ModelConfiguration(
            c2c_config=C2CConfig(
                c2c_models={
                    "model1": ModelDetails(
                        display_name="Model 1",
                        handler="handler1",
                        endpoint="endpoint1",
                        content_type="type1",
                        display_in_reco_explorer=True
                    ),
                    "model2": ModelDetails(
                        display_name="Model 2",
                        handler="handler2",
                        endpoint="endpoint2",
                        content_type="type2",
                        display_in_reco_explorer=True
                    )
                }
            )
        ),
        open_search_config=OpenSearchConfiguration()
    )

    assert result.to_dict() == expected.to_dict()


def test_load_model_configuration__local_u2c_config(local_config_with_u2c):
    result = load_model_configuration(local_config_with_u2c)

    expected = SetupConfiguration(
        model_config=ModelConfiguration(
            u2c_config=U2CConfig(
                u2c_models={
                    "model3": ModelDetails(
                        display_name="Model 3",
                        handler="handler3",
                        endpoint="endpoint3",
                        content_type="type3",
                        display_in_reco_explorer=True
                    ),
                    "model4": ModelDetails(
                        display_name="Model 4",
                        handler="handler4",
                        endpoint="endpoint4",
                        content_type="type4",
                        display_in_reco_explorer=True
                    )
                }
            )
        ),
        open_search_config=OpenSearchConfiguration()
    )

    assert result.to_dict() == expected.to_dict()

def test_load_model_configuration__local_clustering_model_config(local_config_with_clustering_model):
    result = load_model_configuration(local_config_with_clustering_model)

    expected = SetupConfiguration(
        model_config=ModelConfiguration(
            u2c_config=U2CConfig(
                u2c_models={},
                clustering_models={
                    "model5": ModelDetails(
                        display_name="Model 5",
                        handler="handler5",
                        endpoint="endpoint5",
                        content_type="type5",
                        display_in_reco_explorer=True
                    ),
                    "model6": ModelDetails(
                        display_name="Model 6",
                        handler="handler6",
                        endpoint="endpoint6",
                        content_type="type6",
                        display_in_reco_explorer=True
                    )
                }
            )
        ),
        open_search_config=OpenSearchConfiguration()
    )

    assert result.to_dict() == expected.to_dict()


def test_load_model_configuration__remote_index_config(mocker, local_config_without_index):
    mocked_get_model_config = mocker.patch("src.util.file_utils._get_model_config_from_endpoint")
    mocked_get_model_config.return_value = {
        "oss_index": "remote_index"
    }

    result = load_model_configuration(local_config_without_index)

    expected = SetupConfiguration(
        model_config=ModelConfiguration(),
        open_search_config=OpenSearchConfiguration(index="remote_index")
    )

    assert result.to_dict() == expected.to_dict()


def test_load_model_configuration__fetch_from_endpoint(mocker, config_without_model_key):
    mocked_get_model_config = mocker.patch("src.util.file_utils._get_model_config_from_endpoint")
    mocked_get_model_config.return_value = {
        "c2c_models": {
            "remote_model1": {
                "display_name": "Remote Model 1",
                "handler": "remote_handler1",
                "endpoint": "remote_endpoint1",
                "content_type": "remote_type1",
                "display_in_reco_explorer": True
            }
        },
        "u2c_models": {
            "remote_model2": {
                "display_name": "Remote Model 2",
                "handler": "remote_handler2",
                "endpoint": "remote_endpoint2",
                "content_type": "remote_type2",
                "display_in_reco_explorer": True
            }
        },
        "clustering_models": {
            "remote_model3": {
                "display_name": "Remote Model 3",
                "handler": "remote_handler3",
                "endpoint": "remote_endpoint3",
                "content_type": "remote_type3",
                "display_in_reco_explorer": True
            }
        }
    }

    result = load_model_configuration(config_without_model_key)

    expected = SetupConfiguration(
        model_config=ModelConfiguration(
            c2c_config=C2CConfig(
                c2c_models={
                    "remote_model1": ModelDetails(
                        display_name="Remote Model 1",
                        handler="remote_handler1",
                        endpoint="remote_endpoint1",
                        content_type="remote_type1",
                        display_in_reco_explorer=True,
                        default=False,
                        model_name=None,
                        model_path=None,
                        start_color=None,
                        reco_color=None,
                        properties=None,
                        role_arn=None,
                        user_type=None,
                        field_mapping=None
                    )
                }
            ),
            u2c_config=U2CConfig(
                u2c_models={
                    "remote_model2": ModelDetails(
                        display_name="Remote Model 2",
                        handler="remote_handler2",
                        endpoint="remote_endpoint2",
                        content_type="remote_type2",
                        display_in_reco_explorer=True,
                        default=False,
                        model_name=None,
                        model_path=None,
                        start_color=None,
                        reco_color=None,
                        properties=None,
                        role_arn=None,
                        user_type=None,
                        field_mapping=None
                    )
                },
                clustering_models={
                    "remote_model3": ModelDetails(
                        display_name="Remote Model 3",
                        handler="remote_handler3",
                        endpoint="remote_endpoint3",
                        content_type="remote_type3",
                        display_in_reco_explorer=True,
                        default=False,
                        model_name=None,
                        model_path=None,
                        start_color=None,
                        reco_color=None,
                        properties=None,
                        role_arn=None,
                        user_type=None,
                        field_mapping=None
                    )
                }
            )
        ),
        open_search_config=OpenSearchConfiguration(index=None)
    )

    mocked_get_model_config.assert_called_once_with(config_without_model_key)
    assert result.to_dict() == expected.to_dict()


def test_load_model_configuration__merged_configs(mocker):
    local_config = {
        "opensearch": {"index": "local_index"},
        "c2c_config": {
            "c2c_models": {
                "model1": {
                    "display_name": "Local Model",
                    "handler": "local_handler",
                    "endpoint": "local_endpoint",
                    "content_type": "local_type",
                    "display_in_reco_explorer": True
                }
            }
        }
    }

    mocked_get_model_config = mocker.patch("src.util.file_utils._get_model_config_from_endpoint")
    mocked_get_model_config.return_value = {
        "oss_index": "remote_index",
        "c2c_models": ["remote_model1"]
    }

    result = load_model_configuration(local_config)

    expected = SetupConfiguration(
        model_config=ModelConfiguration(
            c2c_config=C2CConfig(
                c2c_models={
                    "model1": ModelDetails(
                        display_name="Local Model",
                        handler="local_handler",
                        endpoint="local_endpoint",
                        content_type="local_type",
                        display_in_reco_explorer=True
                    )
                }
            )
        ),
        open_search_config=OpenSearchConfiguration(index="local_index")
    )

    assert result.to_dict() == expected.to_dict()
