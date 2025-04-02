from collections import namedtuple
import pytest
from src import constants
from src.controller.reco_controller import RecommendationController


@pytest.fixture
def controller() -> RecommendationController:
    controller = RecommendationController(
        config={
            "opensearch.user": "test",
            "opensearch.pass": "test",
            "opensearch.host": "test",
            "opensearch.port": "8080",
            "opensearch.index": "test",
            "opensearch.use_ssl": True,
            "opensearch.field_mapping": {},
        }
    )
    controller.model_type = constants.MODEL_TYPE_C2C
    MockComponent = namedtuple("component", ["visible"])
    controller.components.update(
        {
            "item_choice": {"test": MockComponent(True)},
        }
    )
    return controller


def test_increasing_page_number_succeeds(controller: RecommendationController) -> None:
    controller.increase_page_number()
    assert controller.get_page_number() == 2


def test_get_start_components_succeeds(controller: RecommendationController) -> None:
    component = controller._get_active_start_components()
    assert isinstance(component, list)
    assert component
