import panel as pn
import pytest

from src.view.widgets.text_area_input_widget import TextAreaInputWidget
from test.unit.view.view_test_utils import (
    _validate_widget_type,
    _validate_widget_properties,
)

# Global Constants
TEXT_AREA_INPUT_LABEL = "Text Area Input Label"
TEXT_AREA_INPUT_PLACEHOLDER = "Text Area Input Placeholder"
TEXT_AREA_INPUT_VALIDATOR_FUNCTION_NAME = "Text Area Input Validator Function"
TEXT_AREA_INPUT_ACCESSOR_FUNCTION_NAME = "Text Area Input Accessor Function"
TEXT_AREA_INPUT_URL_PARAMETER = "textAreaInputUrlParameter"
TEXT_AREA_INPUT_RESET_IDENTIFIER = "search_choice"
TEXT_AREA_INPUT_PARAMS_LABEL = "text_input"
TEXT_AREA_MAX_LENGTH = 99_999

FALLBACK_TEXT_AREA_INPUT_LABEL = "Default Text Area Input"
FALLBACK_TEXT_AREA_INPUT_VALIDATOR_FUNCTION_NAME = "_check_text"
FALLBACK_TEXT_AREA_INPUT_ACCESSOR_FUNCTION_NAME = "get_item_by_text"


@pytest.fixture
def create_text_area_input_widget(mocker):
    def _create_text_area_input_widget(config: dict):
        mocker_app = mocker.MagicMock()
        mock_ctrl = mocker.MagicMock()
        return TextAreaInputWidget(mocker_app, mock_ctrl).create(config)
    return _create_text_area_input_widget


def test_default_text_area_input_widget_create(create_text_area_input_widget):
    config = {
        "label": TEXT_AREA_INPUT_LABEL,
        "placeholder": TEXT_AREA_INPUT_PLACEHOLDER,
        "validator_function": TEXT_AREA_INPUT_VALIDATOR_FUNCTION_NAME,
        "accessor_function": TEXT_AREA_INPUT_ACCESSOR_FUNCTION_NAME,
        "url_parameter": TEXT_AREA_INPUT_URL_PARAMETER,
    }

    expected_properties = {
        "name": TEXT_AREA_INPUT_LABEL,
        "placeholder": TEXT_AREA_INPUT_PLACEHOLDER,
        "max_length": TEXT_AREA_MAX_LENGTH,
        "reset_identifier": TEXT_AREA_INPUT_RESET_IDENTIFIER,
        "is_leaf_widget": True,
        "params": {
            "label": TEXT_AREA_INPUT_PARAMS_LABEL,
            "reset_to": "",
            "validator": TEXT_AREA_INPUT_VALIDATOR_FUNCTION_NAME,
            "accessor": TEXT_AREA_INPUT_ACCESSOR_FUNCTION_NAME,
        },
    }

    validate_text_area_input(
        create_text_area_input_widget(config),
        expected_properties
    )


def test_fallback_text_area_input_widget_create(create_text_area_input_widget):
    config = {}

    expected_properties = {
        "name": FALLBACK_TEXT_AREA_INPUT_LABEL,
        "is_leaf_widget": True,
        "reset_identifier": TEXT_AREA_INPUT_RESET_IDENTIFIER,
        "params": {
            "label": TEXT_AREA_INPUT_PARAMS_LABEL,
            "reset_to": "",
            "validator": FALLBACK_TEXT_AREA_INPUT_VALIDATOR_FUNCTION_NAME,
            "accessor": FALLBACK_TEXT_AREA_INPUT_ACCESSOR_FUNCTION_NAME,
        },
    }

    validate_text_area_input(
        create_text_area_input_widget(config),
        expected_properties
    )


def validate_text_area_input(
        text_area_input: pn.widgets.TextAreaInput,
        expected_properties: dict,
):
    _validate_widget_type(
        text_area_input,
        pn.widgets.TextAreaInput, )

    _validate_widget_properties(
        text_area_input,
        expected_properties
    )
