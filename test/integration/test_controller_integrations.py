import pytest
import logging
import constants
from src.controller.reco_controller import RecommendationController
from test.test_util import mock_start_filter_component, mock_start_and_reco_items_with_duplicates


logger = logging.getLogger(__name__)

@pytest.mark.parametrize("start_component, model", [(
    [True, 'genre_users', '_check_category', 'Comedy'],
    ['ARD-ALS-Experiments', constants.MODEL_CONFIG_U2C]
)])
def test_get_items_one_u2c_model_succeeds(u2c_controller: RecommendationController) -> None:
    items = u2c_controller.get_items()
    assert isinstance(items, tuple)
    recos = items[1]
    users = []
    for one_result in recos:
        users.append(one_result[0].id)
    # assert users are correct
    assert len(users) == len(set(users))

@pytest.mark.parametrize("selection_type, start_component, model", [(
    '_by_date',
    {'validator': '_check_date', 'label': 'dateinput', 'accessor': 'get_items_by_date', 'has_paging': True},
    ['All-Mini-LM-en', constants.MODEL_CONFIG_C2C]
)])
def test_get_items_one_c2c_model_by_date_succeeds(c2c_controller: RecommendationController) -> None:
    items = c2c_controller.get_items()
    assert isinstance(items, tuple)


@pytest.mark.parametrize("selection_type, start_component, model", [(
    '_by_date',
    {'validator': '_check_date', 'label': 'dateinput', 'accessor': 'get_items_by_date', 'has_paging': True},
    ['All-Mini-LM-en', constants.MODEL_CONFIG_C2C]
)])
def test_get_items_one_c2c_model_by_date_with_thematic_start_filter_succeeds(
        c2c_controller: RecommendationController) -> None:
    expected_start_theme = 'ARD Retro'
    filter_selection = {
        'label': 'thematicCategories',
        'selected_value': [expected_start_theme]
    }
    mock_filter = mock_start_filter_component(filter_selection)
    c2c_controller.register('item_filter', mock_filter)
    c2c_controller.set_num_items(10)
    response = c2c_controller.get_items()
    assert isinstance(response, tuple)
    models, items, config_identifier = response
    for row in items:
        for item in row:
            if item.position == 'reco':
                continue
            assert expected_start_theme in item.thematicCategories

