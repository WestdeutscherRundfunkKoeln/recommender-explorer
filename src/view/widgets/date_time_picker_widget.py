import panel as pn

from .. import ui_constants as c


class DateTimePickerWidget:
    def __init__(self, reco_explorer_app_instance, controller_instance):
        self.reco_explorer_app_instance = reco_explorer_app_instance
        self.controller_instance = controller_instance

    def create_date_time_picker_component(self, date_time_picker_config):
        """
        Builds a date time picker widget based on the given config from config yaml. This config has to contain a validate function
        name and a accessor function name.

        Args:
            date_time_picker_config (config): config of a date time picker from config yaml.
            Can contain: name, label, validator and accessor function

        Returns:
            date_time_picker_widget (widget): final widget built from given config
        """
        date_time_picker_widget = pn.widgets.DatetimePicker(
            name=date_time_picker_config.get(
                c.DATE_TIME_PICKER_NAME_KEY, c.FALLBACK_DATE_TIME_PICKER_NAME_VALUE
            )
        )
        date_time_picker_widget.params = {
            "validator": date_time_picker_config.get(c.DATE_TIME_PICKER_VALIDATOR_KEY),
            "label": date_time_picker_config.get(c.DATE_TIME_PICKER_LABEL_KEY),
            "accessor": date_time_picker_config.get(c.DATE_TIME_PICKER_ACCESSOR_KEY),
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
