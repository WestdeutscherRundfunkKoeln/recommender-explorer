import glob
import logging
import os
import re
from pathlib import Path

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
