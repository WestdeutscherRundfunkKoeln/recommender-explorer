import panel as pn

from typing import Any, Optional
from view.widgets.widget import UIWidget
from view import ui_constants as c


class RadioBoxWidget(pn.Column, UIWidget):

    def __init__(self, reco_explorer_app_instance, controller_instance):
        pn.Column.__init__(self)
        UIWidget.__init__(self, reco_explorer_app_instance, controller_instance)

    def create(self, config: dict[str, Any]) -> Optional["RadioBoxWidget"]:
        """
        Builds a radio widget based on the given config from config yaml.
        First get the Label Keys from the configured options and store them.
        Then iterate over the options and try to render the configured widgets in these options.
        Connect key and option by adding a watcher to the Label Key Radio Button to the configured
        and build option widget. The watcher controls the visibility of the option widgets. These are
        only visible when connected option label key radio button is selected.

        Args:
            multi_select_config (config): config of a multi select from config yaml.
            If its a filter it should contain a register_as value.

        Returns:
            multi_select_widget (widget): final widget built from given config
        """
        if config.get(c.RADIO_BOX_OPTION_KEY):
            option_widgets_dict = {}
            for option, widgets in config["options"].items():
                widgets_for_option = []
                for widget_config in widgets:
                    widget_for_option = self.reco_explorer_app_instance.build_common_ui_widget_dispatcher(
                        widget_config.get("type"), widget_config
                    )
                    if widget_for_option:
                        widgets_for_option.append(widget_for_option)
                widget_group_wrapper = WidgetGroupWrapper(*widgets_for_option, option_of_widget_group=option)
                option_widgets_dict[option] = widget_group_wrapper

            options = list(option_widgets_dict.keys())
            radio_box_group = pn.widgets.RadioBoxGroup(options=options)

            def show_hide_widgets(
                    event, radio_box_group=radio_box_group, options=option_widgets_dict
            ):
                for option, widgets in options.items():
                    for widget in widgets:
                        self.set_widget_visibility(widget, False)
                        if hasattr(widget, 'reset_identifier'):
                            self.controller_instance.reset_defaults([widget.reset_identifier])

                    selected_option = radio_box_group.value
                    for selected_widget in options.get(selected_option, []):
                        self.set_widget_visibility(selected_widget, True)

            radio_box_group.param.watch(show_hide_widgets, "value")
            show_hide_widgets("value")

            self.append(radio_box_group)
            for widget_wrapper in option_widgets_dict.values():
                self.append(widget_wrapper)

            return self
        else:
            return None

    def set_widget_visibility(self, widget, visibility):
        if isinstance(widget, pn.layout.Row):
            for content in widget:
                content.visible = visibility
        else:
            widget.visible = visibility


class WidgetGroupWrapper(pn.Column):
    def __init__(self, *objects, option_of_widget_group=None, **params):
        super().__init__(*objects, **params)
        self.option_of_widget_group = option_of_widget_group