import pytest
from pathlib import Path

from src.util.file_utils import (
    get_client_options,
    get_configs_from_arg,
    load_ui_config,
    get_client_ident_from_search,
)


@pytest.fixture
def config_dummy():
    return Path(__file__).parent / "config_dummy.yaml"


@pytest.fixture
def config_test():
    return Path(__file__).parent / "config_test.yaml"


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


def test_get_client_options(config_dummy, config_test):
    result = get_client_options({"test": config_test, "dummy": config_dummy})

    assert result == {"test_entry_from_config_file": "test", "Dummy": "dummy"}


def test_get_configs_from_arg__multiple_configs(config_test, config_dummy):
    args = f"config={config_test},{config_dummy}"

    result = get_configs_from_arg(args)

    assert result == ("test", config_test, {"test": config_test, "dummy": config_dummy})


def test_get_configs_from_arg__invalid_config(config_test, config_dummy):
    config_dummy = Path(__file__).parent / "config_dummy.yaml"
    args = f"config=./nonexistent.yaml,{config_dummy}"

    with pytest.raises(Exception):
        get_configs_from_arg(args)


def test_get_client_ident_from_search():
    assert get_client_ident_from_search("?client=test") == "test"
    assert get_client_ident_from_search("?field=test") is None
