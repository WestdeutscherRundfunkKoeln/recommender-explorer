import panel as pn
import pytest

from src.view.widgets.date_time_picker_widget import DateTimePickerWidget
from test.unit.view.view_test_utils import (
    _validate_widget_type,
    _validate_widget_properties,
)

# Global Constants
DATE_TIME_PICKER_NAME = "Date Time Picker Name"
DATE_TIME_PICKER_LABEL = "Date Time Picker Label"
DATE_TIME_PICKER_VALIDATOR_FUNCTION_NAME = "Date Time Validator Function"
DATE_TIME_PICKER_ACCESSOR_FUNCTION_NAME = "Date Time Accessor Function"


@pytest.fixture
def create_date_time_picker_widget(mocker):
    def _create_date_time_picker_widget(config: dict):
        mocker_app = mocker.MagicMock()
        mock_ctrl = mocker.MagicMock()
        return DateTimePickerWidget(mocker_app, mock_ctrl).create(config)
    return _create_date_time_picker_widget


def test_default_date_time_picker_widget_create(create_date_time_picker_widget):
    config = {
        "name": DATE_TIME_PICKER_NAME,
        "label": DATE_TIME_PICKER_LABEL,
        "validator": DATE_TIME_PICKER_VALIDATOR_FUNCTION_NAME,
        "accessor_function": DATE_TIME_PICKER_ACCESSOR_FUNCTION_NAME,
    }

    expected_properties = {
        "name": DATE_TIME_PICKER_NAME,
        "is_leaf_widget": True,
        "reset_identifier": "item_choice",
        "params": {
            "label": DATE_TIME_PICKER_LABEL,
            "reset_to": None,
            "validator": DATE_TIME_PICKER_VALIDATOR_FUNCTION_NAME,
            "accessor": DATE_TIME_PICKER_ACCESSOR_FUNCTION_NAME,
            "has_paging": True
        },
    }

    validate_date_time_picker(create_date_time_picker_widget(config), expected_properties)


def test_fallback_date_time_picker_widget_create(create_date_time_picker_widget):
    config = {
        "validator": DATE_TIME_PICKER_VALIDATOR_FUNCTION_NAME,
        "accessor_function": DATE_TIME_PICKER_ACCESSOR_FUNCTION_NAME,
    }

    expected_properties = {
        "name": "Default Date Time Picker Label",
        "is_leaf_widget": True,
        "reset_identifier": "item_choice",
        "params": {
            "label": None,
            "reset_to": None,
            "validator": DATE_TIME_PICKER_VALIDATOR_FUNCTION_NAME,
            "accessor": DATE_TIME_PICKER_ACCESSOR_FUNCTION_NAME,
            "has_paging": True
        },
    }

    validate_date_time_picker(create_date_time_picker_widget(config), expected_properties)


def test_incorrect_date_time_picker_widget_create(create_date_time_picker_widget):
    config = {
        "name": DATE_TIME_PICKER_NAME,
    }

    expected_properties = {
        "name": DATE_TIME_PICKER_NAME,
        "is_leaf_widget": True,
        "reset_identifier": "item_choice",
        "params": {
            "label": None,
            "reset_to": None,
            "validator": None,
            "accessor": None,
            "has_paging": True
        },
    }

    validate_date_time_picker(create_date_time_picker_widget(config), expected_properties)


def validate_date_time_picker(
        date_time_picker: pn.widgets.DatetimePicker,
        expected_properties: dict,
):
    _validate_widget_type(
        date_time_picker,
        pn.widgets.DatetimePicker, )

    _validate_widget_properties(
        date_time_picker,
        expected_properties
    )
