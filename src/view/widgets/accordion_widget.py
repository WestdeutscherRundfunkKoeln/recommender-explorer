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

        accordion_content = self.hide_trigger_action_widgets(accordion_content)

        if accordion_content:
            all_inner_widgets_column = pn.Column(*accordion_content, sizing_mode='stretch_width')
            accordion_widget.append(
                (
                    config.get(
                        c.ACCORDION_LABEL_KEY, c.FALLBACK_ACCORDION_LABEL_VALUE
                    ),
                    all_inner_widgets_column,
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

    def hide_trigger_action_widgets(self, accordion_content: [any]) -> [any]:
        """
        When there are multiple widgets in one accordion and all of these are multi selects, these
        can trigger visibility of each other by action parameters. Check widgets here for these
        parameters and set alle the ones which can be triggered to visible = false.

        :param accordion_content: List of all widgets inside the accordion
        :return: List of all widgets inside the accordion with hidden widgets where configured
        """
        if all(isinstance(widget, pn.widgets.MultiSelect) for widget in accordion_content) and len(accordion_content) > 1:
            for source_widget in accordion_content:
                if hasattr(source_widget, "action_parameter"):
                    for target_widget_label in source_widget.action_parameter.values():
                        target_widget = self.get_widget_from_content_by_label(
                            accordion_content,
                            target_widget_label
                        )
                        if target_widget:
                            target_widget.visible = False
        return accordion_content

    def get_widget_from_content_by_label(self, accordion_content, target_widget_label):
        """
        Get a widget from a list of widgets with a given label

        :param accordion_content: List of all widgets inside the accordion.
        :param target_widget_label: Label value of the searched widget.
        :return: The widget the given label or None
        """
        for widget in accordion_content:
            if widget.name == target_widget_label:
                return widget
        return None
