import pytest
from src.controller.reco_controller import RecommendationController

@pytest.fixture
def test_increasing_page_number_succeeds(controller: RecommendationController) -> None:
    controller.increase_page_number()
    assert controller.get_page_number() == 2

@pytest.mark.parametrize("start_component", [
    (True, 'genre_users',  '_check_category', 'Comedy'),
])
def test_get_start_components_succeeds(controller: RecommendationController) -> None:
    component = controller._get_active_start_components()
    assert isinstance(component, list)
    assert component

