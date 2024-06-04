from src.util.file_utils import load_ui_config
from pathlib import Path


def test_load_ui_config__valid_config():
    config = {
        "test": "test",
        "ui_config": Path(__file__).parent / "test_ui_config.yaml",
    }

    result = load_ui_config(config)

    assert result == {
        "test": "test",
        "ui_config": {"title": "Test Recommender Explorer"},
        "ui_config.title": "Test Recommender Explorer",
    }


def test_load_ui_config__no_config():
    config = {"test": "test"}

    result = load_ui_config(config)

    assert result == config


def test_load_ui_config__wrong_config():
    config = {
        "test": "test",
        "ui_config": Path(__file__).parent / "this_config_does_not_exist.yaml",
    }

    result = load_ui_config(config)

    assert result == config


def test_load_ui_config__inline_config():
    config = {"test": "test", "ui_config": {"title": "Test Recommender Explorer"}}

    result = load_ui_config(config)

    assert result == config
