import panel as pn


class RadioBoxWidget:
    def __init__(self, reco_explorer_app_instance, controller_instance):
        self.reco_explorer_app_instance = reco_explorer_app_instance
        self.controller_instance = controller_instance

    def create_radio_box_component(self, radio_box_config):
        if radio_box_config.get('options'):
            radio_box_group = pn.widgets.RadioBoxGroup(options=list(radio_box_config['options'].keys()))

            test_dictionary = {}
            for option, widgets in radio_box_config['options'].items():
                widgets_for_option = []
                for widget_config in widgets:
                    widgets_for_option.append(self.reco_explorer_app_instance.build_common_ui_widget_dispatcher(widget_config.get('type'), widget_config))
                test_dictionary[option] = widgets_for_option

            def show_hide_widgets(event, radio_box_group=radio_box_group, options=test_dictionary):
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
                *[element for sublist in test_dictionary.values() for element in sublist]
            )
        else:
            return None
