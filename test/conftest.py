import logging
from test.test_util import (
    mock_date_component,
    mock_model_component,
    mock_user_component,
)

import constants
import pytest
from controller.reco_controller import RecommendationController
from envyaml import EnvYAML

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption("--config", action="store", default="./config_default.yaml")


@pytest.fixture(scope="session")
def config(pytestconfig):
    config_loc = pytestconfig.getoption("config")
    return get_config(config_loc)


def get_config(config) -> EnvYAML:
    config = EnvYAML(config)
    return config


@pytest.fixture
def controller(start_component: list, config: str) -> RecommendationController:
    if not config.get(constants.MODEL_CONFIG_U2C):
        pytest.skip("configuration does not support u2c integration call")
    controller = RecommendationController(config)
    user_choice = mock_user_component(start_component)
    controller.model_type = constants.MODEL_TYPE_U2C
    controller.register("user_choice", user_choice)
    return controller


@pytest.fixture
def u2c_controller(
    start_component: list, model: list, config: str
) -> RecommendationController:
    if not config.get(constants.MODEL_CONFIG_U2C):
        pytest.skip("configuration does not support u2c integration call")
    if not config[constants.MODEL_CONFIG_U2C][constants.MODEL_TYPE_U2C].get(model[0]):
        pytest.skip(
            "model with identifier ["
            + model[0]
            + "] not found in config - cant initialise. check test parameters!"
        )
    controller = RecommendationController(config)
    user_choice = mock_user_component(start_component)
    controller.register("user_choice", user_choice)
    controller.register("model_choice", mock_model_component(model))
    return controller


@pytest.fixture
def c2c_controller(
    selection_type: str, start_component: list, model: list, config: str
) -> RecommendationController:
    if not config[constants.MODEL_CONFIG_C2C][constants.MODEL_TYPE_C2C].get(model[0]):
        pytest.skip(
            "model with identifier ["
            + model[0]
            + "] not found in config - cant initialise. check test parameters!"
        )
    controller = RecommendationController(config)
    if selection_type == "_by_date":
        for position in ["start", "end"]:
            date_choice = mock_date_component(start_component, position)
            controller.register("item_choice", date_choice)
    controller.register("model_choice", mock_model_component(model))
    return controller
