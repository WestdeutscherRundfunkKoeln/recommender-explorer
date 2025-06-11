import json
import logging

from src.constants import (
    MODELS_KEY,
    C2C_MODELS_KEY,
    U2C_MODELS_KEY,
    CLUSTERING_MODELS_KEY,
    S2C_MODELS_KEY
)

logger = logging.getLogger(__name__)

def load_and_validate_model_config(config: dict) -> dict:
    """
    Loads and validates the given model configuration. The function checks if the
    value associated with the key defined by MODELS_KEY in the configuration is a
    string and attempts to parse it as a JSON object. If parsing fails, an error
    is logged, and an exception is raised.

    :param config:
        A dictionary containing the model configuration. The entry associated with
        the MODELS_KEY should ideally be a JSON-compatible string or a pre-parsed
        object.

    :return:
        Returns the updated configuration dictionary with the value for MODELS_KEY
        parsed as a JSON object (if it was provided as a string).

    :raises json.JSONDecodeError:
        Raised if the value associated with MODELS_KEY in the configuration is a
        string but cannot be parsed into a JSON object.
    """
    if isinstance(config[MODELS_KEY], str):
        try:
            config[MODELS_KEY] = json.loads(config[MODELS_KEY])
        except json.JSONDecodeError as e:
            logger.error("Error parsing models config: %s", e)
            raise e
    return config


def get_model_names(config: dict) -> list:
    """
    Extracts and compiles a list of model names from a configuration dictionary.

    This function retrieves model names from a specific configuration dictionary.
    It accesses the 'MODELS_KEY' in the given configuration, processes it through
    helper functions for extracting names under the 'C2C_MODELS_KEY' and
    'U2C_MODELS_KEY' keys, and combines all retrieved model names into a single list.

    :param config: A dictionary containing the configuration, which must include a key,
                   `MODELS_KEY`, that stores information about models.
    :type config: dict
    :return: A list of strings representing all extracted model names from the configuration.
    :rtype: list
    """
    model_names = []
    for key, value in config[MODELS_KEY].items():
        model_names.extend(_extract_model_names(value, C2C_MODELS_KEY))
        model_names.extend(_extract_model_names(value, U2C_MODELS_KEY))
        model_names.extend(_extract_model_names(value, S2C_MODELS_KEY))
    return model_names


def _extract_model_names(models: dict, key: str) -> list:
    """
    Extract model names from a specified key within a dictionary.

    This function navigates through the dictionary structure provided in the
    ``models`` parameter, looks up the value associated with the given ``key``,
    and extracts a list of model names from the corresponding entries.

    :param models: Dictionary containing model configurations organized by keys.
    :type models: dict
    :param key: The key in the dictionary whose model configurations are to be
        processed.
    :type key: str
    :return: A list of model names extracted from the configurations associated
        with the given key.
    :rtype: list
    """
    model_names = []
    for model_key, model_config in models.get(key, {}).items():
        model_names.append(model_config["model_name"])
    return model_names


def get_full_model_config(config: dict) -> dict:
    """
    Aggregates and returns the full model configuration by processing the input
    config to combine model specifications under specific keys (`C2C_MODELS_KEY`
    and `U2C_MODELS_KEY`).

    This function iterates through the models in the provided configuration,
    extracts models under the `C2C_MODELS_KEY` and `U2C_MODELS_KEY`, aggregates
    them into their respective collections, and organizes them into a complete
    model configuration dictionary.

    :param config: A dictionary containing the model configurations, where
                   the key MODELS_KEY maps to a dictionary of individual
                   model specifications.
    :type config: dict

    :return: A dictionary containing the aggregated model configurations
             under the keys `C2C_MODELS_KEY` and `U2C_MODELS_KEY`, if models
             exist for these categories. If none are found, these keys will
             not be included in the returned dictionary.
    :rtype: dict
    """
    full_model_config = {}
    aggregated_c2c_models = {}
    aggregated_u2c_models = {}
    aggregated_cluster_models = {}
    aggregated_s2c_models = {}

    for key, value in config[MODELS_KEY].items():
        _aggregate_models(value, C2C_MODELS_KEY, aggregated_c2c_models)
        _aggregate_models(value, U2C_MODELS_KEY, aggregated_u2c_models)
        _aggregate_models(value, CLUSTERING_MODELS_KEY, aggregated_cluster_models)
        _aggregate_models(value, S2C_MODELS_KEY, aggregated_s2c_models)

    if aggregated_c2c_models:
        full_model_config[C2C_MODELS_KEY] = aggregated_c2c_models
    if aggregated_u2c_models:
        full_model_config[U2C_MODELS_KEY] = aggregated_u2c_models
    if aggregated_cluster_models:
        full_model_config[CLUSTERING_MODELS_KEY] = aggregated_cluster_models
    if aggregated_s2c_models:
        full_model_config[S2C_MODELS_KEY] = aggregated_s2c_models

    return full_model_config


def _aggregate_models(models: dict, key: str, aggregated_models: dict):
    """
    Aggregates models from a nested dictionary under a specific key into the provided
    aggregated models dictionary. This function iterates through the models and adds
    entries to the `aggregated_models` dictionary if they do not already exist.

    :param models: A nested dictionary where models are grouped under specific keys.
    :type models: dict
    :param key: The key in the `models` dictionary to aggregate models from.
    :type key: str
    :param aggregated_models: The dictionary where aggregated results will be
        stored. Existing entries will not be overwritten.
    :type aggregated_models: dict
    :return: None. The `aggregated_models` dictionary is updated directly by reference.
    :rtype: None
    """
    for model_key, model_config in models.get(key, {}).items():
        if model_key not in aggregated_models:
            aggregated_models[model_key] = model_config