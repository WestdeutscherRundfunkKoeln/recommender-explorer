import panel as pn

from view.widgets.widget import UIWidget
from typing import Any


from view import ui_constants as c


class DateTimePickerWidget(UIWidget):
    def create(self, config: dict[str, Any]) -> pn.widgets.DatetimePicker:
        """
        Builds a date time picker widget based on the given config from config yaml. This config has to contain a validate function
        name and a accessor function name.

        Args:
            config (config): config of a date time picker from config yaml.
            Can contain: name, label, validator and accessor function

        Returns:
            date_time_picker_widget (widget): final widget built from given config
        """
        date_time_picker_widget = pn.widgets.DatetimePicker(
            name=config.get(
                c.DATE_TIME_PICKER_NAME_KEY, c.FALLBACK_DATE_TIME_PICKER_NAME_VALUE
            )
        )
        date_time_picker_widget.params = {
            "validator": config.get(c.DATE_TIME_PICKER_VALIDATOR_KEY),
            "label": config.get(c.DATE_TIME_PICKER_LABEL_KEY),
            "accessor": config.get(c.DATE_TIME_PICKER_ACCESSOR_KEY),
            "has_paging": True,
            "reset_to": None,
        }
        date_time_picker_widget.param.watch(
            self.reco_explorer_app_instance.trigger_item_selection,
            "value",
            onlychanged=True,
        )
        self.controller_instance.register("item_choice", date_time_picker_widget)
        return date_time_picker_widget
