import panel as pn

from .. import ui_constants as constants


class MultiSelectionWidget:
    def __init__(self, reco_explorer_app_instance, controller_instance):
        self.reco_explorer_app_instance = reco_explorer_app_instance
        self.controller_instance = controller_instance

    def create_multi_select_options(self, multi_select_option_config):
        """
        Gets a list of options and default option from given config. This config can contain a label
        and a boolean to check if option should be selected initially (as default)

        Args:
            multi_select_option_config (config): config of a list of options from config yaml. Can contain: label and a default bool

        Returns:
            option_list (list): list of all options from multi select widget
            default_option (list): list of all options selected as default
        """
        option_list = []
        default_option = []
        for option in multi_select_option_config.get(constants.MULTI_SELECT_OPTIONS_KEY, ''):
            option_label = option.get(constants.MULTI_SELECT_OPTION_LABEL_KEY)
            if option_label is not None:
                if option.get('item_filter') is not None:
                    option_dictionary = {option_label: option.get('upper_item_filter')}
                    option_list.append(option_dictionary)
                else:
                    option_list.append(option_label)
            option_get_item_defaults = option.get('get_item_defaults')
            if option_get_item_defaults is not None:
                item_defaults = self.controller_instance.get_item_defaults(option_get_item_defaults)
                for item in item_defaults:
                    option_list.append(item)
            if option.get(constants.MULTI_SELECT_DEFAULT_OPTION_KEY, False):
                default_option.append(option_label)
        return option_list, default_option

    def create_multi_select_component(self, multi_select_config):
        """
        Builds a multi select widget based on the given config from config yaml. This config can contain a label
        as headline and a list of options.

        Args:
            multi_select_config (config): config of a text field from config yaml. Can contain: label and a list of options

        Returns:
            text_input (widget): final widget built from given config
            :param multi_select_config:
        """
        option_list, default_option = self.create_multi_select_options(multi_select_config)

        if len(option_list) < 5:
            multi_select_size = len(option_list)
        else:
            multi_select_size = 5

        multi_select_widget = pn.widgets.MultiSelect(
            options=option_list,
            value=default_option,
            size=multi_select_size
        )
        multi_select_widget.params = {
            'label': multi_select_config.get(constants.MULTI_SELECT_LABEL_KEY, constants.FALLBACK_MULTI_SELECT_LABEL_VALUE),
            'reset_to': default_option
        }
        if multi_select_config.get('register_as'):
            if multi_select_config.get('register_as') == 'model_choice':
                model_watcher = multi_select_widget.param.watch(self.reco_explorer_app_instance.trigger_model_choice_new, 'value', onlychanged=True)
                self.controller_instance.register('model_choice', multi_select_widget, model_watcher, self.reco_explorer_app_instance.trigger_model_choice_new)
            elif multi_select_config.get('register_as') == 'item_filter':
                multi_select_widget.param.watch(self.reco_explorer_app_instance.trigger_item_filter_choice, 'value', onlychanged=True)
                self.controller_instance.register('item_filter', multi_select_widget)
            elif multi_select_config.get('register_as') == 'upper_item_filter':
                # self.erzaehlweise.param.watch(self.toggle_genre_selection_by_upper_genre, 'value', onlychanged=True)
                self.controller_instance.register('upper_item_filter', self.reco_explorer_app_instance.erzaehlweise)
        return multi_select_widget
