import pytest
import panel as pn
from unittest.mock import MagicMock

from test.unit.view.widgets.test_text_field_widget import create_text_field_widget
from test.unit.view.widgets.test_date_time_picker_widget import create_date_time_picker_widget
from test.unit.view.widgets.test_text_area_input_widget import create_text_area_input_widget

from view.widgets.radio_box_widget import (
    RadioBoxWidget,
)

from test.unit.view.view_test_utils import (
    _validate_widget_type,
    _get_count_of_a_specific_widget,
)

from test.unit.view.widgets.test_text_field_widget import validate_text_field
from test.unit.view.widgets.test_date_time_picker_widget import validate_date_time_picker
from test.unit.view.widgets.test_text_area_input_widget import validate_text_area_input

RADIO_BOX_CONFIG = {
    "options": {
        "External ID": [
            {
                "type": "text_field",
                "label": "Default Text Input Widget",
                "tooltip": "A Tooltip For This Text Field Widget"
            }
        ],
        "Datum": [
            {
                "type": "date_time_picker",
                "name": "Default Date Time Picker One",
            },
            {
                "type": "date_time_picker",
                "name": "Default Date Time Picker Two",
            },
        ],
        "Textsuche": [
            {
                "type": "text_area_input",
                "label": "Default Text Area Input",
            }
        ],
    },
}



def test_radio_box_widget_create_method(
        create_text_field_widget,
        create_date_time_picker_widget,
        create_text_area_input_widget,
        radio_box_widget_fixture):

    radio_box_widget_to_test = radio_box_widget_fixture(RADIO_BOX_CONFIG)

    # validate (custom) type
    _validate_widget_type(radio_box_widget_to_test, RadioBoxWidget)

    # validate inner types
    assert _get_count_of_a_specific_widget(radio_box_widget_to_test, pn.widgets.RadioBoxGroup) == 1
    # assert _get_count_of_a_specific_widget(radio_box_widget, WidgetGroupWrapper) == len(RADIO_BOX_CONFIG["options"])

    radio_box_group = radio_box_widget_to_test[0]
    # validate wrapper, start at 1: 0 is radio_box_group
    for wrapper in radio_box_widget_to_test[1:]:

        # validate visibility and widget inside wrapper for option
        if wrapper.option_of_widget_group == "External ID":
            for content in wrapper:
                assert _visible_attribute_of(content) is True
                validate_text_field(
                    content,
                    {},
                    "A Tooltip For This Text Field Widget"
                )

        # validate visibility and widget inside wrapper for option
        elif wrapper.option_of_widget_group == "Datum":
            assert len(wrapper) == 2
            for content in wrapper:
                assert _visible_attribute_of(content) is False
                validate_date_time_picker(
                    content,
                    {},
                )

        # validate visibility and widget inside wrapper for option
        elif wrapper.option_of_widget_group == "Textsuche":
            for content in wrapper:
                assert _visible_attribute_of(content) is False
                validate_text_area_input(
                    content,
                    {}
                )

    # select different option and validate resulting visibilities
    radio_box_group.value = "Datum"
    for wrapper in radio_box_widget_to_test[1:]:
        wrapper_contents = wrapper[0]
        if wrapper.option_of_widget_group == "Datum":
            assert _visible_attribute_of(wrapper_contents) is True
        else:
            assert _visible_attribute_of(wrapper_contents) is False


def _visible_attribute_of(wrapper_content: pn.viewable.Viewable) -> bool:
    if isinstance(wrapper_content, pn.Row):
        return wrapper_content[0].visible and wrapper_content[1].visible
    else:
        return wrapper_content.visible
