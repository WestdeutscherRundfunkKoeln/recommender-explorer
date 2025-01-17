from typing import Any

import panel as pn
from view import ui_constants as c
from view.widgets.widget import UIWidget


class TextAreaInputWidget(UIWidget):
    def create(self, config: dict[str, Any]) -> pn.widgets.TextAreaInput:
        text_area_input_widget = pn.widgets.TextAreaInput(
            name=config.get(
                c.TEXT_AREA_INPUT_LABEL_KEY, c.FALLBACK_TEXT_AREA_INPUT_LABEL_VALUE
            ),
            placeholder=config.get(c.TEXT_AREA_INPUT_PLACEHOLDER_KEY, ""),
            max_length=99_999,
            rows= config.get(c.TEXT_AREA_ROWS_NUM, 3),
            max_rows= config.get(c.TEXT_AREA_MAX_ROWS_NUM, 5),
            auto_grow= config.get(c.AUTO_GROW, True)
        )

        text_area_input_widget.params = {
            "validator": config.get(c.TEXT_AREA_INPUT_VALIDATOR_KEY, "_check_text"),
            "accessor": config.get(c.TEXT_AREA_INPUT_ACCESSOR_KEY, "get_item_by_text"),
            "label": "text_input",
            "reset_to": "",
        }

        text_area_input_widget.param.watch(
            self.reco_explorer_app_instance.trigger_item_selection,
            "value",
            onlychanged=True,
        )

        self.controller_instance.register("item_choice", text_area_input_widget)

        url_parameter = config.get(c.TEXT_AREA_INPUT_URL_PARAMETER_KEY, None)
        if url_parameter:
            self.reco_explorer_app_instance.url_parameter_text_field_mapping[
                url_parameter
            ] = text_area_input_widget

        text_area_input_widget.is_leaf_widget = True

        text_area_input_widget.reset_identifier = c.RESET_IDENTIFIER_ITEM_CHOICE


        return text_area_input_widget
