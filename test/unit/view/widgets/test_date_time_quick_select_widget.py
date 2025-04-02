from datetime import datetime, time

import panel as pn
import pytest
from src.view.widgets.date_time_quick_select_widget import DateTimeQuickSelectWidget


def test_date_time_quick_select__all_widgets_found(mocker):
    start = pn.widgets.DatetimePicker()
    start.params = {"label": "start"}

    end = pn.widgets.DatetimePicker()
    end.params = {"label": "end"}

    mock_app = mocker.MagicMock()
    mock_app.config_based_nav_controls = pn.WidgetBox(objects=[])
    mock_ctrl = mocker.MagicMock()
    button = DateTimeQuickSelectWidget(mock_app, mock_ctrl).create(
        {
            "start_picker_label": "start",
            "end_picker_label": "end",
            "start_delta_days": 0,
            "end_delta_days": 0,
        }
    )
    mock_app.config_based_nav_controls = pn.WidgetBox(objects=[start, end])
    assert button is not None
    button.clicks += 1
    assert start.value == datetime.combine(datetime.today(), time.min)
    assert end.value == datetime.combine(datetime.today(), time.max)


def test_date_time_quick_select__no_widgets_found(mocker):
    mock_app = mocker.MagicMock()
    mock_app.config_based_nav_controls = pn.WidgetBox(objects=[])
    mock_ctrl = mocker.MagicMock()
    button = DateTimeQuickSelectWidget(mock_app, mock_ctrl).create(
        {
            "start_picker_label": "start",
            "end_picker_label": "end",
            "start_delta_days": 0,
            "end_delta_days": 0,
        }
    )
    assert button is not None
    with pytest.raises(ValueError):
        button.clicks += 1


def test_date_time_quick_select__invalid_config(mocker):
    mock_app = mocker.MagicMock()
    mock_app.config_based_nav_controls = pn.WidgetBox(objects=[])
    mock_ctrl = mocker.MagicMock()
    button = DateTimeQuickSelectWidget(mock_app, mock_ctrl).create(
        {
            "start_picker_label": "start",
            "end_picker_label": "end",
            "start_delta_days": 0,
            "end_delta_days": 1,
        }
    )
    assert button is None
