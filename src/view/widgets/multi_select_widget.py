import panel as pn

from .filterWidgets.model_choice_widget import ModelChoiceWidget
from .filterWidgets.item_filter_widget import ItemFilterWidget
from .filterWidgets.upper_item_filter import UpperItemFilterWidget
from .filterWidgets.reco_filter_widget import RecoFilterWidget
from .. import ui_constants as c


class MultiSelectionWidget:
    def __init__(self, reco_explorer_app_instance, controller_instance):
        self.reco_explorer_app_instance = reco_explorer_app_instance
        self.controller_instance = controller_instance

    def get_multi_select_options(self, multi_select_config):
        """
        Creates a List of multi select options and default options for the widget based on the given config from config yaml.
        Decides which function is used to create the lists (possible are basic options, dictionary options and default options).
        Also creates and returns a default list, which contains the selected default option(s) for the widget.

        Args:
            multi_select_config (config): config of a multi select from config yaml.

        Returns:
            option_list (list), option_default (list): list of options and option defaults built from given config
        """
        if multi_select_config.get(c.MULTI_SELECT_OPTIONS_KEY):
            option_list = []
            option_default = []
            for option in multi_select_config.get(c.MULTI_SELECT_OPTIONS_KEY, ''):
                option_label = option.get(c.MULTI_SELECT_OPTION_LABEL_KEY)
                if option_label is not None:
                    option_list.append(option_label)
                if option.get(c.MULTI_SELECT_DEFAULT_OPTION_KEY):
                    option_default.append(option_label)
            return option_list, option_default
        elif multi_select_config.get(c.MULTI_SELECT_DICTIONARY_OPTIONS_KEY):
            option_dictionary = {}
            for option in multi_select_config.get(c.MULTI_SELECT_DICTIONARY_OPTIONS_KEY, ''):
                option_dictionary.update(option)
            return option_dictionary, []
        elif multi_select_config.get(c.MULTI_SELECT_OPTIONS_DEFAULT_FUNCTION_KEY):
            option_list = self.controller_instance.get_item_defaults(multi_select_config.get(c.MULTI_SELECT_OPTIONS_DEFAULT_FUNCTION_KEY))
            return option_list, []

    def build_multi_select_widget(self, multi_select_config):
        """
        Builds a multi select widget based on the given config from config yaml.
        Sets options and size and name values for the final widget and sets label into params

        Args:
            multi_select_config (config): config of a multi select from config yaml.

        Returns:
            multi_select_widget (widget): generic multi select widget built from given config
        """
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

    def create_multi_select_component(self, multi_select_config):
        """
        Builds a multi select widget based on the given config from config yaml.
        First only decides which kind of multi select should be built. This is based on the register_as value from config.
        Then init the module class which uses the generic functions in this class to build the specific multi select widget.

        Args:
            multi_select_config (config): config of a multi select from config yaml.
            If its a filter it should contain a register_as value.

        Returns:
            multi_select_widget (widget): final widget built from given config
        """
        multi_select_register_value = multi_select_config.get(c.MULTI_SELECT_REGISTER_AS_KEY)
        if multi_select_register_value == 'item_filter':
            item_filter_widget = ItemFilterWidget(self, self.reco_explorer_app_instance, self.controller_instance)
            return item_filter_widget.create_item_filter_multi_select(multi_select_config)
        elif multi_select_register_value == 'upper_item_filter':
            upper_item_filter_widget = UpperItemFilterWidget(self, self.reco_explorer_app_instance, self.controller_instance)
            return upper_item_filter_widget.create_upper_item_filter_multi_select(multi_select_config)
        elif multi_select_register_value == 'reco_filter':
            reco_filter_widget = RecoFilterWidget(self, self.reco_explorer_app_instance, self.controller_instance)
            return reco_filter_widget.create_reco_filter_multi_select(multi_select_config)
        elif multi_select_register_value == 'model_choice':
            model_choice_widget = ModelChoiceWidget(self, self.reco_explorer_app_instance, self.controller_instance)
            return model_choice_widget.create_model_choice_multi_select(multi_select_config)
        else:
            return self.build_multi_select_widget(multi_select_config)
