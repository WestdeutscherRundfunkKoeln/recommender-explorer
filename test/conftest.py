import pytest
import constants
from envyaml import EnvYAML
from controller.reco_controller import RecommendationController
from test.test_util import mock_user_component, mock_model_component, mock_date_component

@pytest.fixture
def config() -> EnvYAML:
    return get_config()


def get_config(location: bool|str=False) -> EnvYAML:
    if not location:
        configuration_file_name = './config/config_default.yaml'
    else:
        configuration_file_name = location.removeprefix('config=')

    config = EnvYAML(configuration_file_name)
    return config

@pytest.fixture
def controller(start_component: list) -> RecommendationController:
    controller = RecommendationController(get_config())
    user_choice = mock_user_component(start_component)
    controller.model_type = constants.MODEL_TYPE_U2C
    controller.register('user_choice', user_choice)
    return controller

@pytest.fixture
def u2c_controller(start_component: list, model: list) -> RecommendationController:
    controller = RecommendationController(get_config())
    user_choice = mock_user_component(start_component)
    controller.register('user_choice', user_choice)
    controller.register('model_choice', mock_model_component(model))
    return controller
@pytest.fixture
def c2c_controller(selection_type: str, start_component: list, model: list) -> RecommendationController:
    controller = RecommendationController(get_config())
    if selection_type == '_by_date':
        for position in ['start', 'end']:
            date_choice = mock_date_component(start_component, position)
            controller.register('item_choice', date_choice)
    controller.register('model_choice', mock_model_component(model))
    return controller