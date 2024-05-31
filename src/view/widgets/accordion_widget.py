import panel as pn
from typing import Any

from view import ui_constants as c
from view.widgets.widget import UIWidget


class AccordionWidget(UIWidget):
    def create(self, config: dict[str, Any]) -> pn.Accordion:
        """
        Builds a accordion widget based on the given config from config yaml. This config can contain list of contents.
        Content can be every common ui widget

        Args:
            config (config): config of a accordion from config yaml. Can contain: label, active value, a toggle value and a list of content (ui_widgets)

        Returns:
            accordion_widget (widget): final widget built from given config
        """
        accordion_widget = pn.Accordion()
        accordion_content = self.create_accordion_content(
            config.get(c.ACCORDION_CONTENT_KEY, "")
        )
        if accordion_content:
            for component in self.create_accordion_content(
                config.get(c.ACCORDION_CONTENT_KEY, "")
            ):
                accordion_widget.append(
                    (
                        config.get(
                            c.ACCORDION_LABEL_KEY, c.FALLBACK_ACCORDION_LABEL_VALUE
                        ),
                        component,
                    )
                )

        accordion_widget.active = [config.get(c.ACCORDION_ACTIVE_KEY, [])]
        accordion_widget.toggle = config.get(c.ACCORDION_TOGGLE_KEY, False)

        return accordion_widget

    def create_accordion_content(self, accordion_contents_config):
        """
        Creates a list of common ui widgets as content for a accordion widget from config yaml.

        Args:
            accordion_contents_config (config): config of accordion contents from config yaml. Can contain: common ui widget configs

        Returns:
            accordion_content (list): list of common ui widgets as contents for a accordion widget
        """
        accordion_content = []
        if accordion_contents_config:
            for accordion_content_config in accordion_contents_config:
                accordion_content.append(
                    self.reco_explorer_app_instance.build_common_ui_widget_dispatcher(
                        accordion_content_config.get(c.WIDGET_TYPE_KEY, ""),
                        accordion_content_config,
                    )
                )
        return accordion_content

    def create_accordion_reset_buttons(self, accordion_config):
        accordion_reset_buttons = []
        accordion_contents_config = accordion_config.get(c.ACCORDION_CONTENT_KEY)
        accordion_reset_buttons_config = accordion_config.get(
            c.ACCORDION_RESET_BUTTON_TYPE_VALUE
        )
        for accordion_reset_button_config in accordion_reset_buttons_config:
            reset_button_widget = pn.widgets.Button(
                name=accordion_reset_button_config.get(c.ACCORDION_RESET_LABEL_KEY, ""),
                button_type=accordion_reset_button_config.get(
                    c.ACCORDION_RESET_BUTTON_STYLE_KEY, "primary"
                ),
                margin=accordion_reset_button_config.get(
                    c.ACCORDION_RESET_MARGIN_KEY, 0
                ),
            )

            contents_choice_types = []
            if accordion_contents_config:
                for accordion_content_config in accordion_contents_config:
                    accordion_content_type = accordion_content_config.get(
                        c.WIDGET_TYPE_KEY
                    )
                    if accordion_content_type == c.MULTI_SELECT_TYPE_VALUE:
                        contents_choice_types.append("model_choice")

            reset_button_widget.params = {
                "label": "model_resetter",
                "resets": contents_choice_types,
            }

            reset_button_widget.on_click(
                self.reco_explorer_app_instance.trigger_reset_button
            )

            accordion_reset_buttons.append(reset_button_widget)
        if len(accordion_reset_buttons) == 1:
            return accordion_reset_buttons[0]
        elif len(accordion_reset_buttons) > 1:
            # TODO: Not a valid reset button, what now?
            return accordion_reset_buttons[0]
        else:
            return None
