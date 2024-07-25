from typing import Any

import panel as pn
import panel.widgets
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
            all_inner_widgets_column = pn.Column(
                *accordion_content, sizing_mode="stretch_width"
            )
            accordion_widget.append(
                (
                    config.get(c.ACCORDION_LABEL_KEY, c.FALLBACK_ACCORDION_LABEL_VALUE),
                    all_inner_widgets_column,
                )
            )

        accordion_widget.active = [config.get(c.ACCORDION_ACTIVE_KEY, [])]
        accordion_widget.toggle = config.get(c.ACCORDION_TOGGLE_KEY, False)

        accordion_widget.is_leaf_widget = False

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

    def hide_trigger_action_widgets(self, accordion_content: [any]) -> [any]:
        """
        When there are multiple widgets in one accordion and all of these are multi selects, these
        can trigger visibility of each other by action parameters. Check widgets here for these
        parameters and set alle the ones which can be triggered to visible = false.

        :param accordion_content: List of all widgets inside the accordion
        :return: List of all widgets inside the accordion with hidden widgets where configured
        """
        if len(accordion_content) <= 1:
            return accordion_content

        for source_widget in accordion_content:
            source_multi_select_widget = self.get_multi_select_widget_from_row_with_tooltip(source_widget)
            if source_multi_select_widget:
                action_parameter = getattr(source_multi_select_widget, "action_parameter", None)
                if action_parameter is not None:
                    self.hide_target_widgets(accordion_content, source_multi_select_widget)
        return accordion_content

    def hide_target_widgets(self, accordion_content, source_widget):
        """
        Set all target widgets, which were defined in the action parameters in the source widget to
        visible = False, so that they are initially hidden.

        :param accordion_content: List of all widgets inside the accordion
        :param source_widget: The widget which has the action parameters attached
        """
        for target_widget_label in source_widget.action_parameter.values():
            target_widget = self.get_widget_from_content_by_label(
                accordion_content, target_widget_label
            )
            if target_widget:
                target_widget.visible = False

    def get_widget_from_content_by_label(self, accordion_content, target_widget_label):
        """
        Get a widget from a list of widgets with a given label

        :param accordion_content: List of all widgets inside the accordion.
        :param target_widget_label: Label value of the searched widget.
        :return: The widget the given label or None
        """
        for widget in accordion_content:
            multi_select_widget = self.get_multi_select_widget_from_row_with_tooltip(widget)
            if multi_select_widget is not None and multi_select_widget.name == target_widget_label:
                return widget
        return None

    def get_multi_select_widget_from_row_with_tooltip(self, widget):
        """
        Method to check if the given widget is a multi-select widget with a tooltip in a row layout.

        :param widget: The widget to be checked.
        :type widget: panel.Row
        :return: The multi-select widget if it matches the conditions, otherwise None.
        """
        if isinstance(widget, pn.Row) and len(widget) == 2 and isinstance(widget[0], panel.widgets.select.MultiSelect):
            return widget[0]
        else:
            return None
