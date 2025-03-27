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


def load_model_configuration(config: dict[str, str]) -> dict[str, str | None] | Any:
    """
    Parses the model configuration from the input configuration dictionary or requests configuration
    from an external endpoint. Returns a dictionary containing model-specific configurations if found.
    Logs the loading process for debugging purposes.

    :param config: A dictionary containing configuration details.
    :type config: dict[str, str]

    :return: A dictionary containing parsed model-specific configurations or the result of an
        external endpoint response. Each entry may include `c2c_config` or `u2c_config` keys.
    :rtype: dict[str, str | None] | Any
    """
    result = {}
    if "c2c_config" in config:
        result["c2c_config"] = config["c2c_config"]
        logger.info("Load c2c model configuration from config yaml file.")
        logger.info("c2c_config: %s", result['c2c_config'])
    if "u2c_config" in config:
        result["u2c_config"] = config["u2c_config"]
        logger.info("Load u2c model configuration from config yaml file.")
        logger.info("u2c_config: %s", result['u2c_config'])
    if "clustering_models" in config:
        result["u2c_config"] = result.get("u2c_config", {})
        if isinstance(result["u2c_config"], dict):
            result["u2c_config"]["clustering_models"] = config["clustering_models"]
        logger.info("Load clustering models from config yaml file.")
        logger.info("clustering_models: %s", config["clustering_models"])


    if result:
        return result

    response_from_endpoint = _get_model_config_from_endpoint(config)

    if "c2c_models" in response_from_endpoint:
        result["c2c_config"] = {"c2c_models": response_from_endpoint["c2c_models"]}
        logger.info("Load c2c model configuration from embedding microservice.")
        logger.info("c2c_config: %s", result['c2c_config'])
    if "u2c_models" in response_from_endpoint:
        result["u2c_config"] = {"u2c_models": response_from_endpoint["u2c_models"]}
        logger.info("Load u2c model configuration from embedding microservice.")
        logger.info("u2c_config: %s", result['u2c_config'])
    if "clustering_models" in response_from_endpoint:
        result["u2c_config"] = result.get("u2c_config", {})
        if isinstance(result["u2c_config"], dict):
            result["u2c_config"]["clustering_models"] = response_from_endpoint["clustering_models"]
        logger.info("Load clustering models from embedding microservice.")
        logger.info("clustering_models: %s", response_from_endpoint["clustering_models"])

    return result



