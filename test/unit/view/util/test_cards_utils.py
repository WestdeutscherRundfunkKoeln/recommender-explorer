import panel as pn
from unittest.mock import patch, MagicMock

import sys
import os

sys.path.append(os.path.abspath('../src/'))

from test.unit.view.widgets.test_text_field_widget import create_text_field_widget
from test.unit.view.widgets.test_date_time_picker_widget import create_date_time_picker_widget
from test.unit.view.widgets.test_text_area_input_widget import create_text_area_input_widget
from test.unit.view.widgets.test_radio_box_widget import RADIO_BOX_CONFIG

from view.widgets.radio_box_widget import WidgetGroupWrapper, RadioBoxWidget

from view.cards.cards_utils import (
    _extract_widgets_from_radio_box_widget,
    _get_target_widget_from_radio_box_set_value_and_select_option
)


def create_radio_box_widget_for_cards_test(
        config: dict,
        create_text_field_widget,
        create_date_time_picker_widget,
        create_text_area_input_widget
) -> RadioBoxWidget:
    def mock_build_common_ui_widget_dispatcher(widget_type, widget_config):
        if widget_type == "text_field":
            return create_text_field_widget(widget_config)
        elif widget_type == 'date_time_picker':
            return create_date_time_picker_widget(widget_config)
        elif widget_type == 'text_area_input':
            return create_text_area_input_widget(widget_config)

    reco_explorer_app_instance = MagicMock()
    reco_explorer_app_instance.build_common_ui_widget_dispatcher.side_effect = mock_build_common_ui_widget_dispatcher

    controller_instance = MagicMock()

    widget = RadioBoxWidget(reco_explorer_app_instance, controller_instance)
    return widget.create(config)


def test_extract_widgets_from_radio_box_widget(
        create_text_field_widget,
        create_date_time_picker_widget,
        create_text_area_input_widget
):
    test_widget = create_radio_box_widget_for_cards_test(
        RADIO_BOX_CONFIG,
        create_text_field_widget,
        create_date_time_picker_widget,
        create_text_area_input_widget
    )

    options = list(RADIO_BOX_CONFIG['options'].keys())

    radio_box_group, widget_group_wrappers = _extract_widgets_from_radio_box_widget(test_widget)

    assert radio_box_group.options == options
    assert len(options) == len(widget_group_wrappers)


@patch('view.cards.cards_utils.get_first_widget_by_accessor_function')
def test_get_target_widget_from_radio_box_set_value_and_select_option(
        mock_get_first_widget,
        create_text_field_widget,
        create_date_time_picker_widget,
        create_text_area_input_widget,
):
    test_widget = create_radio_box_widget_for_cards_test(
        RADIO_BOX_CONFIG,
        create_text_field_widget,
        create_date_time_picker_widget,
        create_text_area_input_widget
    )

    radio_box_group, widget_group_wrappers = _extract_widgets_from_radio_box_widget(test_widget)

    # mock a target widget, set it as result for patched get_first_widget_by_accessor_function
    config_of_target_widget = RADIO_BOX_CONFIG['options']["External ID"][0]
    target_widget = create_text_field_widget(config_of_target_widget)
    mock_get_first_widget.return_value = target_widget
    external_id = "123581321"

    _get_target_widget_from_radio_box_set_value_and_select_option(
        radio_box_group, widget_group_wrappers, external_id
    )

    mock_get_first_widget.assert_called()
    assert target_widget.value == external_id
    assert radio_box_group.value == widget_group_wrappers[0].option_of_widget_group
