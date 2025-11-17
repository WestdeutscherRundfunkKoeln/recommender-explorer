import glob
import logging
import os
import re
from pathlib import Path

from envyaml import EnvYAML

import constants

from exceptions.config_error import ConfigError
from view import ui_constants
from util.s3_utils import (
    download_s3_object_to_temp,
    list_s3_objects,
)

logger = logging.getLogger(__name__)


def get_all_config_files(path) -> list:
    pattern = os.path.dirname(path) + "/" + "config_[a-z]*.yaml"
    all_configs = glob.glob(pattern)
    return all_configs


def _process_s3_config_item(item: str) -> list[Path]:
    """
    Process an S3 URI and download matching configuration files.

    :param item: S3 URI (specific object or prefix)
    :return: List of downloaded file paths
    :raises Exception: If no configuration files are found
    """
    matches = list_s3_objects(item, pattern="config_*.yaml")
    if not matches:
        if item.lower().endswith(".yaml"):
            matches = [item]
        else:
            raise Exception(
                f"No configuration files matched under {item}. Ensure keys are named like 'config_<client>.yaml'."
            )

    downloaded_paths = []
    for uri in matches:
        tmp = download_s3_object_to_temp(uri)
        downloaded_paths.append(tmp)
    return downloaded_paths


def _process_local_config_item(item: str) -> list[Path]:
    """
    Process a local file path or directory and collect configuration files.

    :param item: Local file path or directory
    :return: List of configuration file paths
    :raises Exception: If the path does not exist
    """
    item_path = Path(item)
    if item_path.is_dir():
        return [f for f in sorted(item_path.glob("config_*.yaml"))]
    elif item_path.is_file():
        return [item_path]
    else:
        raise ConfigError(
            f"Config path not found: {item}. Provide an existing local file/dir or an s3:// URI."
        )


def _extract_client_name_from_path(path: Path) -> str:
    """
    Extract client name from a configuration file path.

    :param path: Configuration file path
    :return: Client name extracted from the path or filename
    """
    try:
        return get_client_from_path(full_path=str(path))
    except ConfigError:
        return os.path.splitext(os.path.basename(str(path)))[0]


def get_configs_from_arg(arg: str) -> tuple[str, Path, dict[str, Path]]:
    config_args = arg.removeprefix("config=").split(",")

    collected_paths: list[Path] = []

    for item in filter(None, (x.strip() for x in config_args)):
        if item.startswith("s3://"):
            collected_paths.extend(_process_s3_config_item(item=item))
        else:
           collected_paths.extend(_process_local_config_item(item=item))

    if not collected_paths:
        raise ConfigError("No configuration files resolved from provided inputs.")

    key_valuev_pairs = [
        (_extract_client_name_from_path(path=path), path)
        for path in collected_paths
    ]

    return *key_valuev_pairs[0], dict(key_valuev_pairs)


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
        raise ConfigError("Client could not be matched from path [" + full_path + "]")


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
    """
    Load configuration strictly from the provided YAML file.
    External UI config files referenced by a string path are no longer supported.
    The UI configuration must be embedded inline under the `ui_config` key.
    """
    config = EnvYAML(full_path).export()
    # Warn if a legacy path-based UI config is provided
    ui_cfg = config.get(ui_constants.UI_CONFIG_KEY)
    if isinstance(ui_cfg, str):
        logger.warning(
            "Ignoring external UI config file reference '%s'. Inline UI config under 'ui_config' must be provided.",
            ui_cfg,
        )

    return config



