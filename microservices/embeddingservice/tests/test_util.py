import pytest
import json
from src.model_config_utils import (
    load_and_validate_model_config,
    get_model_names,
    get_full_model_config
)

def test_load_and_validate_model_config_valid_string():
    config = {"models": '{"key1": {"name": "model1"}, "key2": {"name": "model2"}}'}
    validated_config = load_and_validate_model_config(config)

    assert isinstance(validated_config["models"], dict)
    assert "key1" in validated_config["models"]
    assert validated_config["models"]["key1"]["name"] == "model1"

def test_load_and_validate_model_config_already_valid_dict():
    config = {"models": {"key1": {"name": "model1"}, "key2": {"name": "model2"}}}
    validated_config = load_and_validate_model_config(config)

    assert isinstance(validated_config["models"], dict)
    assert validated_config["models"]["key2"]["name"] == "model2"


def test_load_and_validate_model_config_invalid_string():
    config = {"models": '{"key1": {"name": "model1" "key2": {"name": "model2"}}'}  # Invalid JSON
    with pytest.raises(json.JSONDecodeError):
        load_and_validate_model_config(config)

def test_load_and_validate_model_config_missing_key():
    config = {}
    with pytest.raises(KeyError):
        load_and_validate_model_config(config)

def test_get_model_names_with_models():
    config = {
        "models": {
            "key1": {
                "c2c_models": {"model_a": {"model_name": "model1"}},
                "u2c_models": {"model_b": {"model_name": "model2"}}
            },
            "key2": {
                "c2c_models": {"model_c": {"model_name": "model3"}}
            },
        }
    }
    model_names = get_model_names(config)
    assert sorted(model_names) == sorted(["model1", "model2", "model3"])


def test_get_model_names_no_models():
    config = {
        "models": {
            "key1": {},
            "key2": {}
        }
    }
    model_names = get_model_names(config)
    assert model_names == []


def test_get_full_model_config_with_data():
    config = {
        "models": {
            "key1": {
                "c2c_models": {"model_a": {"model_name": "model1"}},
                "u2c_models": {"model_b": {"model_name": "model2"}}
            },
            "key2": {
                "c2c_models": {"model_c": {"model_name": "model3"}},
                "u2c_models": {"model_b": {"model_name": "model2"}},  # Duplicate
            },
        }
    }
    aggregated_config = get_full_model_config(config)
    assert "c2c_models" in aggregated_config
    assert "u2c_models" in aggregated_config
    assert len(aggregated_config["c2c_models"]) == 2
    assert len(aggregated_config["u2c_models"]) == 1
    assert aggregated_config["u2c_models"]["model_b"]["model_name"] == "model2"


def test_get_full_model_config_no_models():
    config = {"models": {"key1": {}, "key2": {}}}
    aggregated_config = get_full_model_config(config)
    assert aggregated_config == {}
