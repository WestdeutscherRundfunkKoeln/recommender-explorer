from datetime import datetime, timedelta, time
import logging
from typing import Any, cast

import panel as pn
from src.view import ui_constants as c
from src.view.util.view_utils import find_widget_by_type_and_label
from src.view.widgets.widget import UIWidget

logger = logging.getLogger(__name__)


class DateTimeQuickSelect(UIWidget):
    def create(self, config: dict[str, Any]) -> pn.widgets.Button | None:
        try:
            start_date_picker = self.get_date_picker(
                config.get("start_date_picker_label", "Start Date Time")
            )

            end_date_picker = self.get_date_picker(
                config.get("end_date_picker_label", "End Date Time")
            )

            daystart_start_date = get_start_datetime(config)
            dayend_end_date = get_end_datetime(config)
        except ValueError as e:
            logger.error("Failed to create datetime quick select", exc_info=True)
            return

        if daystart_start_date > dayend_end_date:
            logger.error("Start date is greater than end date.")
            return

        def _set_date_range(event):
            start_date_picker.value = daystart_start_date
            end_date_picker.value = dayend_end_date

        button = pn.widgets.Button(name=config.get("label", "New Year"))
        button.on_click(_set_date_range)

        return button

    def get_date_picker(self, label: str) -> pn.widgets.DatetimePicker:
        date_picker = find_widget_by_type_and_label(
            self.reco_explorer_app_instance.config_based_nav_controls,
            pn.widgets.DatetimePicker,
            label,
        )
        if not date_picker:
            raise ValueError("Could not find date time picker widget: %s", label)
        return date_picker


def get_start_datetime(config: dict[str, Any]) -> datetime:
    return _get_datetime_from_config(config, "start_date_delta_days", time.min)


def get_end_datetime(config: dict[str, Any]) -> datetime:
    return _get_datetime_from_config(config, "end_date_delta_days", time.max)


def _get_datetime_from_config(
    config: dict[str, Any], key: str, _time: time
) -> datetime:
    delta_days = config.get(key)
    if not delta_days:
        raise ValueError(f"{key} not found in config.")
    return datetime.combine(datetime.today() - timedelta(days=delta_days), _time)
