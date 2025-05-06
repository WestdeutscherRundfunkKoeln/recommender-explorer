import glob
import logging
import os
import re
from pathlib import Path
from typing import Any

import httpx
from envyaml import EnvYAML

import constants
from exceptions.config_error import ConfigError
from view import ui_constants
from src.util.dataclasses.setup_configuration_data_class import SetupConfiguration
from src.util.dataclasses.model_configuration_data_class import ModelConfiguration
from src.util.dataclasses.opensearch_configuration_data_class import OpenSearchConfiguration

logger = logging.getLogger(__name__)


def get_all_config_files(path) -> list:
    pattern = os.path.dirname(path) + "/" + "config_[a-z]*.yaml"
    all_configs = glob.glob(pattern)
    return all_configs


def get_configs_from_arg(arg: str) -> tuple[str, Path, dict[str, Path]]:
    config_paths = arg.removeprefix("config=").split(",")
    for config_path in config_paths:
        if not os.path.isfile(config_path):
            raise Exception("Config file not found at path [" + config_path + "]")
    kv_pairs = [
        (get_client_from_path(config_path), Path(config_path))
        for config_path in config_paths
    ]
    return *kv_pairs[0], dict(kv_pairs)


def get_config_from_search(
    search: str, config_full_paths: dict[str, str]
) -> tuple[str, str] | None:
    client = get_client_ident_from_search(search)
    if not client:
        logger.error("No client identifier found in search")
        return

    if client not in config_full_paths:
        raise ConfigError(f"Config for client {client}", {})
    return client, config_full_paths[client]


def get_client_from_path(full_path):
    match = re.search(r"/config_(\w+)\.yaml$", full_path)

    # Check if a match is found and return the config name
    if match:
        return match.group(1)
    else:
        raise Exception("Client could not be matched from path [" + full_path + "]")


def get_client_ident_from_search(search: str) -> str | None:
    for pair in search.removeprefix("?").split("&"):
        param, val = pair.split("=")
        if param == constants.CLIENT_IDENTIFIER:
            return val


def get_client_options(all_configs: dict[str, str]) -> dict[str, str]:
    return {
        EnvYAML(config_path).get("display_name", client.capitalize()): client
        for client, config_path in all_configs.items()
    }


def load_config(full_path: Path) -> dict[str, str]:
    config = EnvYAML(full_path).export()

    return load_ui_config(config, full_path)


def load_ui_config(config: dict[str, str], full_path: Path) -> dict[str, str]:
    ui_config_path = config.get(ui_constants.UI_CONFIG_KEY)

    if not ui_config_path:
        logger.warning("UI config not found in config file %s.", full_path)
        return config

    if isinstance(ui_config_path, dict):
        logger.warning("UI config seems to be defined inline")
        return config

    full_ui_config_path = Path(full_path.parent, ui_config_path)
    if not full_ui_config_path.exists():
        logger.warning("UI config file at %s not found.", full_ui_config_path)
        return config

    ui_config = EnvYAML(full_ui_config_path, include_environment=False).export()
    config.update(ui_config)
    return config


def load_deployment_version_config(config: dict[str, str]) -> dict[str, str]:
    """
    This method updates the provided configuration dictionary with the deployment version information
    from the "version_information.yaml" file located at "config/wdr/version_information.yaml".
    This file gets added by the build pipeline. The updated configuration dictionary is then returned.

    :param config: A dictionary containing the current configuration.
    :return: A dictionary containing the updated configuration with the deployment version information.
    """
    version_config = {}
    try:
        version_config = EnvYAML(
            "config/wdr/version_information.yaml", include_environment=False
        ).export()
    except FileNotFoundError:
        logger.info("No version information yaml found. Only used for dev environment")

    config.update(version_config)
    return config

def _construct_endpoint_url(base_url: str, model_config_key: str | None) -> str:
    """
    Constructs a complete endpoint URL for fetching model configuration. The URL
    constructed depends on the presence of a specific model configuration key. If
    the key is provided, the function includes it in the endpoint URL. Otherwise,
    it defaults to the URL for retrieving all model configurations.

    :param base_url: The base URL of the API.
    :type base_url: str
    :param model_config_key: The key identifying the specific model configuration.
        If None, fetches all configurations.
    :type model_config_key: str | None
    :return: The complete endpoint URL.
    :rtype: str
    """
    if model_config_key:
        logger.info("Fetching model configuration for specified key: %s", model_config_key)
        return f"{base_url}/model_config/{model_config_key}"
    else:
        logger.info("Fetching all model configurations.")
        return f"{base_url}/model_config"


def _get_model_config_from_endpoint(config: dict[str, str]) -> dict[str, Any]:
    """
    Fetches the model configuration from a remote API endpoint using the provided
    configuration dictionary. This function verifies the input configuration for
    required keys, constructs the endpoint URL, and performs an HTTP GET request
    to retrieve the model configuration. Any issues during the HTTP request or
    JSON parsing will result in a custom `ConfigError` being raised with specific
    details.

    :param config: A dictionary containing configuration data, primarily including
        keys related to the API such as "ingest" with sub-keys "base_url_embedding"
        for the base URL and "api_key" for the authentication key.
    :type config: dict[str, str]

    :return: A dictionary representing the JSON response of the API, containing the
        model configuration details.
    :rtype: dict[str, Any]

    :raises ConfigError: Raises a `ConfigError` if mandatory keys ("base_url_embedding",
        "api_key") are missing in the provided configuration or if any error occurs
        during the HTTP request to the endpoint (e.g., timeout, HTTP error, or
        JSON decoding failure).
    """
    ingest_config = config.get("ingest", {})
    base_url = ingest_config.get("base_url_embedding")
    api_key = ingest_config.get("api_key")
    if not base_url or not api_key:
        raise ConfigError("Missing base URL or API key in configuration.",{})

    endpoint_url = _construct_endpoint_url(base_url, config.get("model_config_key"))

    try:
        response = httpx.get(
            endpoint_url,
            timeout=10,
            headers={"x-api-key": api_key}
        )
        return response.json()
    except httpx.TimeoutException:
        raise ConfigError(
            "Request to endpoint timed out. Check the network or server status.",
            {"timeout": True}
        )
    except httpx.HTTPError as e:
        raise ConfigError(
            f"Request failed with status code {e.response.status_code}: {e.response.text}",
            {"status_code": e.response.status_code, "details": e.response.text}
        )
    except ValueError as e:
        raise ConfigError(
            f"Failed to parse the JSON response: {str(e)}",
            {"response_text": response.text}
        )

def load_model_configuration(config: dict[str, Any]) -> SetupConfiguration:
    local_setup_config = SetupConfiguration.from_dict(config)

    try:
        endpoint_response = _get_model_config_from_endpoint(config)
        endpoint_config = {}

        if "oss_index" in endpoint_response:
            endpoint_config["opensearch"] = {"index": endpoint_response["oss_index"]}

        if "c2c_models" in endpoint_response:
            endpoint_config["c2c_config"] = {"c2c_models": endpoint_response["c2c_models"]}

        if "u2c_models" in endpoint_response:
            endpoint_config["u2c_config"] = {"u2c_models": endpoint_response["u2c_models"]}

        if "clustering_models" in endpoint_response:
            endpoint_config["u2c_config"] = endpoint_config.get("u2c_config", {})
            endpoint_config["u2c_config"]["clustering_models"] = endpoint_response["clustering_models"]

        remote_setup_config = SetupConfiguration.from_dict(endpoint_config)

        merged_config = SetupConfiguration(
            model_config=ModelConfiguration(
                c2c_config=local_setup_config.model_config.c2c_config or remote_setup_config.model_config.c2c_config,
                u2c_config=local_setup_config.model_config.u2c_config or remote_setup_config.model_config.u2c_config
            ),
            open_search_config=OpenSearchConfiguration(
                index=local_setup_config.open_search_config.index or remote_setup_config.open_search_config.index
            )
        )
        logger.info("Merged model configuration from local config file and remote endpoints.")
        return merged_config

    except ConfigError as e:
        logger.warning(f"Failed to fetch configuration from endpoint: {e.message}. Using local configuration only.")
        return local_setup_config
    except Exception as e:
        logger.warning(f"Unexpected error while fetching remote configuration: {str(e)}. Using local configuration only.")
        return local_setup_config



