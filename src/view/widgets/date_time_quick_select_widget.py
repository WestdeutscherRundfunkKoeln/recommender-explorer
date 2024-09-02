from datetime import datetime, timedelta, time
import logging
from typing import Any

import panel as pn
from view import ui_constants as c
from view.util.view_utils import find_widget_by_type_and_label
from view.widgets.widget import UIWidget

logger = logging.getLogger(__name__)


class DateTimeQuickSelectWidget(UIWidget):
    def create(self, config: dict[str, Any]) -> pn.widgets.Button | None:
        start_picker_label = config.get(
            c.DATE_TIME_QUICK_SELECT_START_PICKER_LABEL_KEY, "start"
        )
        end_picker_label = config.get(
            c.DATE_TIME_QUICK_SELECT_END_PICKER_LABEL_KEY, "end"
        )
        start_delta = timedelta(
            config.get(c.DATE_TIME_QUICK_SELECT_START_DELTA_DAYS, 0)
        )
        end_delta = timedelta(config.get(c.DATE_TIME_QUICK_SELECT_END_DELTA_DAYS, 0))

        if start_delta < end_delta:
            logger.error("Start date is greater than end date.")
            return

        def _set_date_range(event):
            self.set_picker(start_picker_label, start_delta, time.min)
            self.set_picker(end_picker_label, end_delta, time.max)

        button = pn.widgets.Button(
            name=config.get(c.DATE_TIME_QUICK_SELECT_LABEL_KEY, "Today")
        )
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
