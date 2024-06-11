from pathlib import Path

from src.util.file_utils import get_client_options, load_ui_config


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


def test_get_client_options():
    result = get_client_options(Path(__file__).parent / "config_test.yaml")

    assert result == {"test_entry_from_config_file": "test", "Dummy": "dummy"}
