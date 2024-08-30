from datetime import datetime, timedelta, time
import logging
from typing import Any

import panel as pn
from src.view import ui_constants as c
from src.view.util.view_utils import find_widget_by_type_and_label
from src.view.widgets.widget import UIWidget

logger = logging.getLogger(__name__)


class DateTimeQuickSelect(UIWidget):
    def create(self, config: dict[str, Any]) -> pn.widgets.Button | None:
        start_picker_label = config.get("start_picker_label", "Start Date Time")
        end_picker_label = config.get("end_picker_label", "End Date Time")
        start_delta = timedelta(config.get("start_delta", 0))
        end_delta = timedelta(config.get("end_delta", 0))

        if start_delta < end_delta:
            logger.error("Start date is greater than end date.")
            return

        def _set_date_range(event):
            self.set_picker(start_picker_label, start_delta, time.min)
            self.set_picker(end_picker_label, end_delta, time.max)

        button = pn.widgets.Button(name=config.get("label", "New Year"))
        button.on_click(_set_date_range)
        return button

    def set_picker(self, label: str, delta_days: timedelta, _time: time) -> None:
        picker = self.get_date_picker(label)
        if picker is None:
            raise ValueError(f"Could not find {label}")
        picker.value = datetime.combine(datetime.today() - delta_days, _time)

    def get_date_picker(self, label: str) -> pn.widgets.DatetimePicker | None:
        return find_widget_by_type_and_label(
            self.reco_explorer_app_instance.config_based_nav_controls,
            pn.widgets.DatetimePicker,
            label,
        )
