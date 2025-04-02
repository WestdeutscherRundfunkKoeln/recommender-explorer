import pytest
import panel as pn

from src.view.widgets.text_field_widget import TextFieldWidget
from test.unit.view.view_test_utils import (
    _validate_widget_type,
    _validate_widget_properties,
)

# Global Constants
TEXT_FIELD_LABEL = "Text Field Label"
TEXT_FIELD_PLACEHOLDER = "A Text Field Placeholder"
TEXT_FIELD_VALIDATOR_FUNCTION_NAME = "_check_text"
TEXT_FIELD_ACCESSOR_FUNCTION_NAME = "get_item_by_crid"
TEXT_FIELD_URL_PARAMETER_NAME = "urlParameterTest"
TEXT_FIELD_FILTER_COMPONENT_GROUP = "reco_filter"
TEXT_FIELD_ITEM_RESET_IDENTIFIER = "item_choice"
TEXT_FIELD_TOOLTIP_TEXT = "A Tooltip For This Text Field Widget"
TEXT_FIELD_TOOLTIP_FALLBACK_TEST = "!! Hinterlegen Sie bitte einen beschreibenden Text zu diesem Parameter in der UI-Configuration.!!"


@pytest.fixture
def create_text_field_widget(mocker):
    def _create_text_field_widget(config):
        mocker_app = mocker.MagicMock()
        mock_ctrl = mocker.MagicMock()
        return TextFieldWidget(mocker_app, mock_ctrl).create(config)
    return _create_text_field_widget


def test_default_text_field(create_text_field_widget):
    config = {
        "type": "text_field",
        "label": TEXT_FIELD_LABEL,
        "placeholder": TEXT_FIELD_PLACEHOLDER,
        "validator_function": TEXT_FIELD_VALIDATOR_FUNCTION_NAME,
        "accessor_function": TEXT_FIELD_ACCESSOR_FUNCTION_NAME,
        "url_parameter": TEXT_FIELD_URL_PARAMETER_NAME,
        "tooltip": TEXT_FIELD_TOOLTIP_TEXT
    }

    expected_properties = {
        "name": TEXT_FIELD_LABEL,
        "placeholder": TEXT_FIELD_PLACEHOLDER,
        "reset_identifier": TEXT_FIELD_ITEM_RESET_IDENTIFIER,
        "is_leaf_widget": True,
        "params": {
            "label": TEXT_FIELD_LABEL,
            "reset_to": "",
            "validator": TEXT_FIELD_VALIDATOR_FUNCTION_NAME,
            "accessor": TEXT_FIELD_ACCESSOR_FUNCTION_NAME,
            "has_paging": False
        },
    }

    validate_text_field(create_text_field_widget(config), expected_properties, TEXT_FIELD_TOOLTIP_TEXT)


def test_text_field_fallback(create_text_field_widget):
    config = {
        "validator_function": TEXT_FIELD_VALIDATOR_FUNCTION_NAME,
        "accessor_function": TEXT_FIELD_ACCESSOR_FUNCTION_NAME,
    }

    expected_properties = {
        "name": "",
        "is_leaf_widget": True,
        "params": {
            "label": "",
            "reset_to": "",
        },
    }

    validate_text_field(create_text_field_widget(config), expected_properties, TEXT_FIELD_TOOLTIP_FALLBACK_TEST)


def test_text_field_with_component_group(create_text_field_widget):
    config = {
        "label": TEXT_FIELD_LABEL,
        "component_group": TEXT_FIELD_FILTER_COMPONENT_GROUP,
        "tooltip": TEXT_FIELD_TOOLTIP_TEXT
    }

    expected_properties = {
        "name": TEXT_FIELD_LABEL,
        "reset_identifier": TEXT_FIELD_FILTER_COMPONENT_GROUP,
        "is_leaf_widget": True,
        "params": {
            "label": TEXT_FIELD_LABEL,
            "reset_to": "",
        },
    }

    validate_text_field(create_text_field_widget(config), expected_properties, TEXT_FIELD_TOOLTIP_TEXT)


def validate_text_field(
        text_field: pn.Row,
        expected_properties: dict,
        text_field_tooltip_text: str):
    _validate_text_field_row_length(text_field)

    _validate_widget_type(text_field[0], pn.widgets.TextInput)

    _validate_widget_properties(
        text_field[0],
        expected_properties
    )

    _validate_tooltip_icon_widget(text_field[1], text_field_tooltip_text)


def _validate_text_field_row_length(text_field_row: pn.Row):
    _validate_widget_type(text_field_row, pn.Row)
    assert len(text_field_row) == 2


def _validate_tooltip_icon_widget(tooltip_icon_widget: pn.viewable.Viewable, expected_value: str):
    _validate_widget_type(tooltip_icon_widget, pn.widgets.TooltipIcon)
    expected_properties = {
        "value": expected_value
    }
    _validate_widget_properties(
        tooltip_icon_widget,
        expected_properties
    )
