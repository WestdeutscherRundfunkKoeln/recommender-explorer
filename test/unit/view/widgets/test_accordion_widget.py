import pytest
import panel as pn

from unittest.mock import patch, MagicMock

import src.view.widgets.accordion_widget
from src.view.widgets.accordion_widget import (
    AccordionWidget,
    AccordionWidgetWithCards,
)

from test.unit.view.view_test_utils import (
    _validate_widget_type,
)


def mock_ui_widget():
    widget = MagicMock()
    widget.__getitem__.return_value = widget
    return widget


@patch('src.view.widgets.accordion_widget.AccordionWidget.create_accordion_content')
@patch('src.view.widgets.accordion_widget.AccordionWidget.hide_trigger_action_widgets')
def test_accordion_widget_create(
        mock_create_accordion_content,
        mock_hide_trigger_action_widgets,
        mocker,
):
    mocker_app = mocker.MagicMock()
    mocker_ctrl = mocker.MagicMock()

    config = {
        "type": "accordion",
        "label": "Test Accordion",
        "content": "content_gets_mocked",
        "active": 2,
    }
    instance = AccordionWidget(mocker_app, mocker_ctrl)
    accordion_widget_to_test = instance.create(config)

    mock_create_accordion_content.assert_called()
    mock_hide_trigger_action_widgets.assert_called()
    _validate_widget_type(accordion_widget_to_test, pn.Accordion)
    _validate_widget_type(accordion_widget_to_test[0], pn.Column)
    assert accordion_widget_to_test.active == [2]
    assert accordion_widget_to_test.hidden_label == "Test Accordion"


def test_accordion_widget_with_cards_with_toggle_activated_and_several_active_cards_fails(mocker):
    with pytest.raises(Exception) as e_info:
            # mock errroneous config { active: [0,1], toggle: True }
            ### create the AccordionsWithCards widget (instance.create(config) )

        mocker_app = mocker.MagicMock()
        mocker_ctrl = mocker.MagicMock()

        config = {
            "type": "accordion",
            "label": "Test Accordion",
            "options": "content_gets_mocked",
            "active": [0,1],
        }

        def mock_get_config_value_side_effect(*args, **kwargs):
            if args[2] == int:
                return 2
            elif args[2] == bool:
                return True
            else:
                return None

        mock_get_config_value = mocker.patch.object(
            src.view.widgets.accordion_widget.AccordionWidgetWithCards, 'get_config_value',
        )
        mock_get_config_value.side_effect = mock_get_config_value_side_effect

        mock_create_accordion_content = mocker.patch.object(
            src.view.widgets.accordion_widget.AccordionWidget, 'create_accordion_content',
            return_value=[]
        )

        instance = AccordionWidgetWithCards(mocker_app, mocker_ctrl)

        accordion_widget_with_cards_to_test = instance.create(config)

        #assert not (isinstance(accordion_widget_with_cards_to_test.active, list) and len(
            #accordion_widget_with_cards_to_test.active) > 1 and accordion_widget_with_cards_to_test.toggle), \
            #"Assertion failed: active is a list with more than 1 element and toggle is True"


def test_accordion_widget_with_cards_create(mocker):
    mocker_app = mocker.MagicMock()
    mocker_ctrl = mocker.MagicMock()

    config = {
        "type": "accordion",
        "label": "Test Accordion",
        "options": "content_gets_mocked",
        "active": 2,
    }

    def mock_get_config_value_side_effect(*args, **kwargs):
        if args[2] == int:
            return 2
        elif args[2] == bool:
            return True
        else:
            return None

    mock_get_config_value = mocker.patch.object(
        src.view.widgets.accordion_widget.AccordionWidgetWithCards, 'get_config_value',
    )
    mock_get_config_value.side_effect = mock_get_config_value_side_effect

    mock_create_accordion_content = mocker.patch.object(
        src.view.widgets.accordion_widget.AccordionWidget, 'create_accordion_content',
        return_value=[]
    )

    instance = AccordionWidgetWithCards(mocker_app, mocker_ctrl)

    accordion_widget_with_cards_to_test = instance.create(config)


    mock_create_accordion_content.assert_called()
    mock_get_config_value.assert_called()
    _validate_widget_type(accordion_widget_with_cards_to_test, pn.Accordion)
    assert accordion_widget_with_cards_to_test.active == [2]
