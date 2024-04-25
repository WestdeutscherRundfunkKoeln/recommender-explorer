import panel as pn

from .. import ui_constants as c


class MultiSelectionWidget:
    def __init__(self, reco_explorer_app_instance, controller_instance):
        self.reco_explorer_app_instance = reco_explorer_app_instance
        self.controller_instance = controller_instance

    def list_to_tuple_string(self, lst):
        """
        Convert a list to a string representation of a tuple.

        Args:
            lst (list): The list to be converted.

        Returns:
            str: String representation of a tuple with elements enclosed in single quotes.
        """
        tuple_str = ', '.join(f"'{item}'" for item in lst)
        return f"({tuple_str})"

    def get_basic_options(self, multi_select_config):
        option_list = []
        option_default = []
        for option in multi_select_config.get(c.MULTI_SELECT_OPTIONS_KEY, ''):
            option_label = option.get(c.MULTI_SELECT_OPTION_LABEL_KEY)
            if option_label is not None:
                option_list.append(option_label)
            if option.get(c.MULTI_SELECT_DEFAULT_OPTION_KEY, False):
                option_default.append(option_label)
        return option_list, option_default

    def get_dictionary_options(self, multi_select_config):
        option_dictionary = {}
        for option in multi_select_config.get(c.MULTI_SELECT_DICTIONARY_OPTIONS_KEY, ''):
            option_dictionary.update(option)
        return option_dictionary, []

    def get_default_options_from_controller(self, multi_select_config):
        option_list = self.controller_instance.get_item_defaults(multi_select_config.get(c.MULTI_SELECT_OPTIONS_DEFAULT_FUNCTION_KEY))
        return option_list, []

    def get_multi_select_options(self, multi_select_config):
        if multi_select_config.get(c.MULTI_SELECT_OPTIONS_KEY):
            return self.get_basic_options(multi_select_config)
        elif multi_select_config.get(c.MULTI_SELECT_DICTIONARY_OPTIONS_KEY):
            return self.get_dictionary_options(multi_select_config)
        elif multi_select_config.get(c.MULTI_SELECT_OPTIONS_DEFAULT_FUNCTION_KEY):
            return self.get_default_options_from_controller(multi_select_config)

    def build_multi_select_widget(self, multi_select_config):
        options, default = self.get_multi_select_options(multi_select_config)
        multi_select_label = multi_select_config.get(c.MULTI_SELECT_LABEL_KEY, '')
        if options:
            if len(options) < 5:
                multi_select_size = len(options)
            else:
                multi_select_size = 5

            multi_select_widget = pn.widgets.MultiSelect(
                options=options,
                value=default,
                size=multi_select_size,
                name=multi_select_label
            )
            multi_select_widget.params = {
                'label': multi_select_label,
                'reset_to': default
            }
            return multi_select_widget
        else:
            return None

    def create_item_filter_multi_select(self, multi_select_config):
        item_filter_widget = self.build_multi_select_widget(multi_select_config)
        if item_filter_widget:
            item_filter_widget.param.watch(self.reco_explorer_app_instance.trigger_item_filter_choice, 'value', onlychanged=True)
            self.controller_instance.register('item_filter', item_filter_widget)
            return item_filter_widget
        else:
            return None

    def create_upper_item_filter_multi_select(self, multi_select_config):
        upper_item_filter_widget = self.build_multi_select_widget(multi_select_config)
        linked_filter_name = multi_select_config.get(c.MULTI_SELECT_LINKED_FILTER_NAME_KEY)
        filter_category = multi_select_config.get(c.MULTI_SELECT_FILTER_CATEGORY)
        if upper_item_filter_widget and linked_filter_name and filter_category:
            if linked_filter_name and linked_filter_name:
                upper_item_filter_widget.param.watch(
                    lambda event: self.load_options_after_filter_got_set(linked_filter_name, filter_category, upper_item_filter_widget, event),
                    'value',
                    onlychanged=True
                )
                self.controller_instance.register('upper_item_filter', upper_item_filter_widget)
                return upper_item_filter_widget
        else:
            return None

    def set_params_for_reco_filter(self, reco_filter_widget, reco_filter_label, action_list, action_2_list):
        if len(action_list) > 0 and len(action_2_list) > 0:
            reco_filter_widget.params = {
                'label': reco_filter_label,
                'visible_action': tuple(action_list),
                'visible_action_2': tuple(action_2_list),
                'reset_to': None
            }
        elif len(action_list) > 0:
            reco_filter_widget.params = {
                'label': reco_filter_label,
                'visible_action': tuple(action_list),
                'reset_to': None
            }
        else:
            reco_filter_widget.params = {
                'label': reco_filter_label,
                'reset_to': []
            }
        return reco_filter_widget

    def create_reco_filter_multi_select(self, multi_select_config):
        reco_filter_widget = self.build_multi_select_widget(multi_select_config)
        reco_filter_label = multi_select_config.get(c.MULTI_SELECT_LABEL_KEY)
        action_list = []
        action_2_list = []
        if multi_select_config.get('visible_action'):
            for action_1 in multi_select_config.get('visible_action'):
                action_list.append(action_1.get('action_name'))
        if multi_select_config.get('visible_action_2'):
            for action_2 in multi_select_config.get('visible_action_2'):
                action_2_list.append(action_2.get('action_name'))
        if reco_filter_widget and reco_filter_label:
            reco_filter_widget = self.set_params_for_reco_filter(reco_filter_widget, reco_filter_label, action_list, action_2_list)

            reco_filter_watcher = reco_filter_widget.param.watch(self.reco_explorer_app_instance.trigger_reco_filter_choice, 'value', onlychanged=True)
            self.controller_instance.register('reco_filter', reco_filter_widget, reco_filter_watcher, self.reco_explorer_app_instance.trigger_reco_filter_choice)
            return reco_filter_widget
        else:
            return None

    def create_model_choice_multi_select(self, multi_select_config):
        model_choice_widget = self.build_multi_select_widget(multi_select_config)
        if model_choice_widget:
            model_watcher = model_choice_widget.param.watch(self.reco_explorer_app_instance.trigger_model_choice_new, 'value', onlychanged=True)
            self.controller_instance.register('model_choice', model_choice_widget, model_watcher, self.reco_explorer_app_instance.trigger_model_choice_new)
            return model_choice_widget
        return None

    def create_multi_select_component(self, multi_select_config):
        multi_select_register_value = multi_select_config.get(c.MULTI_SELECT_REGISTER_AS_KEY)
        if multi_select_register_value == 'item_filter':
            return self.create_item_filter_multi_select(multi_select_config)
        elif multi_select_register_value == 'upper_item_filter':
            return self.create_upper_item_filter_multi_select(multi_select_config)
        elif multi_select_register_value == 'reco_filter':
            return self.create_reco_filter_multi_select(multi_select_config)
        elif multi_select_register_value == 'model_choice':
            return self.create_model_choice_multi_select(multi_select_config)
        else:
            return self.build_multi_select_widget(multi_select_config)

    def load_options_after_filter_got_set(self, target_widget_name, category, filter_widget, event):
        upper_category_widget = filter_widget
        target_widget = self.find_widget_by_name_recursive(self.reco_explorer_app_instance.config_based_nav_controls, target_widget_name)
        if event.type == 'changed':
            if category == 'genres':
                target_widget.value = self.controller_instance.get_genres_and_subgenres_from_upper_category(upper_category_widget.value, category)

    def find_widget_by_name_recursive(self, widget, target_name):
        # Check if the current widget has the target name
        if hasattr(widget, 'name') and widget.name == target_name:
            return widget

        # If the current widget has nested widgets, iterate over them
        if hasattr(widget, 'objects'):
            for obj in widget.objects:
                # Recursively call the function to search within nested widgets
                found_widget = self.find_widget_by_name_recursive(obj, target_name)
                if found_widget is not None:
                    return found_widget

        return None
