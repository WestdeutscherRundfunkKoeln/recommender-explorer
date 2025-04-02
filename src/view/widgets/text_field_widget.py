from typing import Any
import panel as pn
from view import ui_constants as c
from view.widgets.widget import UIWidget


class TextFieldWidget(UIWidget):
    def create(self, config: dict[str, Any]) -> pn.Row:
        """
        Builds a textField widget based on the given config from config yaml. When a url_parameter value is given
        in the config, this string gets saved in a dictionary (url_parameter_text_field_mapping) to be used when
        Application loads. Also at least a label or a placeholder must be in config. Validator function and accessor function
        must be in config.

        Args:
            text_field_config (config): config of a text field from config yaml.
            Can contain: label, placeholder, validator_function, accessor_function and url_parameter

        Returns:
            text_input_widget (widget): final widget built from given config
        """
        text_field_label = config.get(c.TEXT_INPUT_LABEL_KEY, "")
        text_field_placeholder = config.get(c.TEXT_INPUT_PLACEHOLDER_KEY, "")
        text_field_accessor = config.get(c.TEXT_INPUT_ACCESSOR_KEY)
        text_field_validator = config.get(c.TEXT_INPUT_VALIDATOR_KEY)
        url_parameter = config.get(c.TEXT_INPUT_URL_PARAMETER_KEY)
        component_group = config.get(c.TEXT_INPUT_COMPONENT_GROUP_KEY)
        visible = config.get(c.VISIBLE, False)

        text_input_widget = pn.widgets.TextInput(
            placeholder=text_field_placeholder,
            name=text_field_label,
            width=c.FILTER_WIDTH,
            visible = visible,
        )

        if text_field_label == "" and text_field_placeholder != "":
            text_field_label = text_field_placeholder
        if (
            text_field_accessor is not None
            and text_field_validator is not None
            and text_field_label != ""
        ):
            component_group = "item_choice"

        text_input_widget.params = {
            "label": text_field_label,
            "reset_to": "",
        }
        if url_parameter is not None:
            self.reco_explorer_app_instance.url_parameter_text_field_mapping[
                url_parameter
            ] = text_input_widget
        match component_group:
            case "item_choice":
                text_input_widget.params.update(
                    {
                        "validator": text_field_validator,
                        "accessor": text_field_accessor,
                        "has_paging": False,
                    }
                )
                text_input_widget.param.watch(
                    self.reco_explorer_app_instance.trigger_item_selection,
                    "value",
                    onlychanged=True,
                )
                self.controller_instance.register(component_group, text_input_widget)
                text_input_widget.reset_identifier = c.RESET_IDENTIFIER_ITEM_CHOICE
            case "reco_filter" | "item_filter":
                text_input_watcher = text_input_widget.param.watch(
                    self.reco_explorer_app_instance.trigger_reco_filter_choice,
                    "value",
                    onlychanged=True,
                )
                self.controller_instance.register(
                    component_group,
                    text_input_widget,
                    text_input_watcher,
                    self.reco_explorer_app_instance.trigger_reco_filter_choice,
                )
                if component_group == "reco_filter":
                    text_input_widget.reset_identifier = c.RESET_IDENTIFIER_RECO_FILTER
                elif component_group == "item_filter":
                    text_input_widget.reset_identifier = c.RESET_IDENTIFIER_ITEM_FILTER

        text_input_widget.is_leaf_widget = True

        tooltip_value = config.get(c.TEXT_INPUT_TOOLTIP_KEY, c.TOOLTIP_FALLBACK)
        tooltip = None if not tooltip_value else pn.widgets.TooltipIcon(value=tooltip_value)

        return pn.Row(text_input_widget, tooltip)

