import panel as pn

from .. import ui_constants as c


class TextFieldWidget:
    def __init__(self, reco_explorer_app_instance, controller_instance):
        self.reco_explorer_app_instance = reco_explorer_app_instance
        self.controller_instance = controller_instance

    def create_text_field_component(self, text_field_config):
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
        text_field_label = text_field_config.get(c.TEXT_INPUT_LABEL_KEY, "")
        text_field_placeholder = text_field_config.get(c.TEXT_INPUT_PLACEHOLDER_KEY, "")
        text_field_accessor = text_field_config.get(c.TEXT_INPUT_ACCESSOR_KEY)
        text_field_validator = text_field_config.get(c.TEXT_INPUT_VALIDATOR_KEY)
        url_parameter = text_field_config.get(c.TEXT_INPUT_URL_PARAMETER_KEY)

        text_input_widget = pn.widgets.TextInput(
            placeholder=text_field_placeholder, name=text_field_label
        )

        if text_field_label == "" and text_field_placeholder != "":
            text_field_label = text_field_placeholder

        if (
            text_field_accessor is not None
            and text_field_validator is not None
            and text_field_label != ""
        ):
            text_input_widget.params = {
                "validator": text_field_validator,
                "accessor": text_field_accessor,
                "label": text_field_label,
                "has_paging": False,
                "reset_to": "",
            }
            text_input_widget.param.watch(
                self.reco_explorer_app_instance.trigger_item_selection,
                "value",
                onlychanged=True,
            )
            self.controller_instance.register("item_choice", text_input_widget)
            if url_parameter is not None:
                self.reco_explorer_app_instance.url_parameter_text_field_mapping[
                    url_parameter
                ] = text_input_widget
            return text_input_widget
        else:
            return text_input_widget
