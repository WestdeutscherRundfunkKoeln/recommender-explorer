import panel as pn

from .. import ui_constants as c


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
        for option in multi_select_option_config.get(c.MULTI_SELECT_OPTIONS_KEY, ''):
            option_label = option.get(c.MULTI_SELECT_OPTION_LABEL_KEY)
            if option_label is not None:
                    option_list.append(option_label)
            option_get_item_defaults = option.get(c.MULTI_SELECT_ITEM_DEFAULTS_KEY)
            if option_get_item_defaults is not None:
                item_defaults = self.controller_instance.get_item_defaults(option_get_item_defaults)
                for item in item_defaults:
                    option_list.append(item)
            if option.get(c.MULTI_SELECT_DEFAULT_OPTION_KEY, False):
                default_option.append(option_label)
        return option_list, default_option

    def create_multi_select_options_from_dictionary(self, multi_select_option_config):
        option_dictionary = {}
        default_option = []
        for option in multi_select_option_config.get(c.MULTI_SELECT_OPTIONS_KEY, ''):
            if option.get(c.MULTI_SELECT_OPTION_LABEL_KEY) and option.get(c.MULTI_SELECT_UPPER_ITEM_FILTER_KEY):
                option_dictionary[option.get(c.MULTI_SELECT_OPTION_LABEL_KEY)] = option.get(c.MULTI_SELECT_UPPER_ITEM_FILTER_KEY)
        return option_dictionary, default_option

    def build_multi_select_widget(self, options, default_option, label):
        if len(options) < 5:
            multi_select_size = len(options)
        else:
            multi_select_size = 5

        multi_select_widget = pn.widgets.MultiSelect(
            options=options,
            value=default_option,
            size=multi_select_size
        )
        multi_select_widget.params = {
            'label': label,
            'reset_to': default_option
        }
        return multi_select_widget

    def create_item_filter_multi_select(self, multi_select_config, multi_select_label):
        if multi_select_config.get(c.MULTI_SELECT_OPTIONS_DEFAULT_KEY):
            option_list = self.controller_instance.get_item_defaults(multi_select_config.get(c.MULTI_SELECT_OPTIONS_DEFAULT_KEY))
            item_filter_widget = self.build_multi_select_widget(option_list, [], multi_select_label)
            item_filter_widget.param.watch(self.reco_explorer_app_instance.toggle_genre_selection_by_upper_genre, 'value', onlychanged=True)
            self.controller_instance.register('item_filter', item_filter_widget)
            return item_filter_widget
        else:
            return None

    def create_upper_item_filter_multi_select(self, multi_select_config, multi_select_label):
        option_dictionary, default_option = self.create_multi_select_options_from_dictionary(multi_select_config)
        upper_item_filter_widget = self.build_multi_select_widget(option_dictionary, default_option, multi_select_label)
        upper_item_filter_widget.param.watch(self.reco_explorer_app_instance.toggle_genre_selection_by_upper_genre, 'value', onlychanged=True)
        self.controller_instance.register('upper_item_filter', upper_item_filter_widget)
        return upper_item_filter_widget

    def create_model_choice_multi_select(self, multi_select_config, multi_select_label):
        option_list, default_option = self.create_multi_select_options(multi_select_config)
        model_choice_widget = self.build_multi_select_widget(option_list, default_option, multi_select_label)
        model_watcher = model_choice_widget.param.watch(self.reco_explorer_app_instance.trigger_model_choice_new, 'value', onlychanged=True)
        self.controller_instance.register('model_choice', model_choice_widget, model_watcher, self.reco_explorer_app_instance.trigger_model_choice_new)
        return model_choice_widget

    def create_multi_select_component(self, multi_select_config):
        multi_select_label = multi_select_config.get(c.MULTI_SELECT_LABEL_KEY, c.FALLBACK_MULTI_SELECT_LABEL_VALUE)
        multi_select_register_value = multi_select_config.get(c.MULTI_SELECT_REGISTER_AS_KEY)
        if multi_select_register_value == 'item_filter':
            return self.create_item_filter_multi_select(multi_select_config, multi_select_label)
        elif multi_select_register_value == 'upper_item_filter':
            return self.create_upper_item_filter_multi_select(multi_select_config, multi_select_label)
        elif multi_select_register_value == 'model_choice':
            return self.create_model_choice_multi_select(multi_select_config, multi_select_label)
        else:
            option_list, default_option = self.create_multi_select_options(multi_select_config)
            return self.build_multi_select_widget(option_list, default_option, multi_select_label)
