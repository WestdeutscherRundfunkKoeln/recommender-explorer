from panel.widgets import MultiSelect
import pytest
from src.controller.reco_controller import RecommendationController
from src.view.RecoExplorerApp import RecoExplorerApp
from src.view.widgets.multi_select_widget import ModelChoiceWidget


TEST_CONFIG = {
    "c2c_config": {
        "c2c_models": {
            "PA-Service-Collaborative-Var-I": {
                "display_name": "PA-Service-Collaborative-Var-I",
                "handler": "NnSeekerPaService@model.rest.nn_seeker_paservice",
                "endpoint": "https://test.io",
                "start_color": "#CFB284",  # dark yellow,
                "reco_color": "#F6E3BA",  # light yellow,
                "content_type": "ContentItemDto",
                "properties": {
                    "auth_header": "ARD",
                    "auth_header_value": "access",
                    "param_similarityType": "collaborative",
                    "param_modelType": "collab_matrix_model_episode_var1",
                },
                "default": True,
            },
            "PA-Service-Collaborative-Var-II": {
                "display_name": "PA-Service-Collaborative-Var-II",
                "handler": "NnSeekerPaService@model.rest.nn_seeker_paservice",
                "endpoint": "https://test.io",
                "start_color": "#5F84A2",  # dark blue
                "reco_color": "#B7D0E1",  # light blue
                "content_type": "ContentItemDto",
                "properties": {
                    "auth_header": "ARD",
                    "auth_header_value": "access",
                    "param_similarityType": "collaborative",
                    "param_modelType": "collab_matrix_model_episode_var2",
                },
                "default": False,
            },
            "PA-Service-Collaborative-Var-III": {
                "display_name": "PA-Service-Collaborative-Var-III",
                "handler": "NnSeekerPaService@model.rest.nn_seeker_paservice",
                "endpoint": "https://test.io",
                "start_color": "#4B6043",  # dark green
                "reco_color": "#75975E",  # light green
                "content_type": "ContentItemDto",
                "properties": {
                    "auth_header": "ARD",
                    "auth_header_value": "access",
                    "param_similarityType": "collaborative",
                    "param_modelType": "collab_matrix_model_episode_var3",
                },
                "default": False,
            },
            "PA-Service-Collaborative-Var-IV": {
                "display_name": "PA-Service-Collaborative-Var-IV",
                "handler": "NnSeekerPaService@model.rest.nn_seeker_paservice",
                "endpoint": "https://test.io",
                "start_color": "#BB6859",  # dark red
                "reco_color": "#F78D7D",  # light red
                "content_type": "ContentItemDto",
                "properties": {
                    "auth_header": "ARD",
                    "auth_header_value": "access",
                    "param_similarityType": "collaborative",
                    "param_modelType": "collab_matrix_model_episode_var4",
                },
                "default": False,
            },
        }
    }
}

TEST_UI_CONFIG = {
    "type": "multi_select",
    "tooltip": "Modell das für die Embedding-Generierung verwendet wurde.",
    "label": "c2c_config",
    "register_as": "model_choice",
    "options": [
        {"display_name": "PA-Service-Collaborative-Var-I", "default": True},
        {"display_name": "PA-Service-Collaborative-Var-II"},
        {"display_name": "PA-Service-Collaborative-Var-III"},
        {"display_name": "PA-Service-Collaborative-Var-IV"},
    ],
}


@pytest.fixture
def mock_controller(mocker):
    mock = mocker.MagicMock(spec=RecommendationController)
    mock.config = TEST_CONFIG
    return mock


@pytest.fixture
def mock_view(mocker):
    mock = mocker.MagicMock(spec=RecoExplorerApp)
    mock.config = TEST_CONFIG
    return mock


def test_model_select_widget(
    mock_view: RecoExplorerApp, mock_controller: RecommendationController
):
    widget = ModelChoiceWidget(
        reco_explorer_app_instance=mock_view, controller_instance=mock_controller
    )
    result = widget.create(TEST_UI_CONFIG)
    assert result is not None
    assert isinstance(result, MultiSelect)
    assert result.values == [
        "PA-Service-Collaborative-Var-I",
        "PA-Service-Collaborative-Var-II",
        "PA-Service-Collaborative-Var-III",
        "PA-Service-Collaborative-Var-IV",
    ]
    assert result.value[0] == "PA-Service-Collaborative-Var-I"
