import panel as pn


from .. import ui_constants as c

class RadioBoxWidget:
    def __init__(self, reco_explorer_app_instance, controller_instance):
        self.reco_explorer_app_instance = reco_explorer_app_instance
        self.controller_instance = controller_instance

    def create_radio_box_component(self, radio_box_config):
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
        if radio_box_config.get(c.RADIO_BOX_OPTION_KEY):
            radio_box_group = pn.widgets.RadioBoxGroup(options=list(radio_box_config['options'].keys()))

            result_dictionary = {}
            for option, widgets in radio_box_config['options'].items():
                widgets_for_option = []
                for widget_config in widgets:
                    widget_for_option = self.reco_explorer_app_instance.build_common_ui_widget_dispatcher(widget_config.get('type'), widget_config)
                    if widget_for_option:
                        widgets_for_option.append(widget_for_option)
                result_dictionary[option] = widgets_for_option

            def show_hide_widgets(event, radio_box_group=radio_box_group, options=result_dictionary):
                for option, widgets in options.items():
                    for widget in widgets:
                        widget.visible = False
                    selected_option = radio_box_group.value
                    for selected_widget in options.get(selected_option, []):
                        selected_widget.visible = True

            radio_box_group.param.watch(show_hide_widgets, 'value')
            show_hide_widgets('value')

            return pn.Column(
                radio_box_group,
                *[element for sublist in result_dictionary.values() for element in sublist]
            )
        else:
            return None
