from typing import Any
import panel as pn

from view.widgets.widget import UIWidget
from view import ui_constants as c


class MultiSelectionWidget(UIWidget):
    def get_multi_select_options(
        self, multi_select_config
    ) -> tuple[list[str] | dict[str, str], list[str]]:
        """
        Creates a List of multi select options and default options for the widget based on the given config from config yaml.
        Decides which function is used to create the lists (possible are basic options, dictionary options and default options).
        Also creates and returns a default list, which contains the selected default option(s) for the widget.

        Args:
            multi_select_config (config): config of a multi select from config yaml.

        Returns:
            option_list (list), option_default (list): list of options and option defaults built from given config
        """
        if c.MULTI_SELECT_OPTIONS_KEY in multi_select_config:
            option_list = []
            option_default = []
            for option in multi_select_config.get(c.MULTI_SELECT_OPTIONS_KEY, ""):
                option_label = option.get(c.MULTI_SELECT_OPTION_LABEL_KEY)
                if option_label is not None:
                    option_list.append(option_label)
                if c.MULTI_SELECT_DEFAULT_OPTION_KEY in option:
                    option_default.append(option_label)
            return option_list, option_default
        elif c.MULTI_SELECT_DICTIONARY_OPTIONS_KEY in multi_select_config:
            return {
                k: v
                for option in multi_select_config[c.MULTI_SELECT_DICTIONARY_OPTIONS_KEY]
                for k, v in option.items()
            }, []
        elif c.MULTI_SELECT_OPTIONS_DEFAULT_FUNCTION_KEY in multi_select_config:
            return self.controller_instance.get_item_defaults(
                multi_select_config[c.MULTI_SELECT_OPTIONS_DEFAULT_FUNCTION_KEY]
            ), []
        return [], []

    def build_multi_select_widget(self, config) -> pn.widgets.MultiSelect | None:
        """
        Builds a multi select widget based on the given config from config yaml.
        Sets options and size and name values for the final widget and sets label into params

        Args:
            multi_select_config (config): config of a multi select from config yaml.

        Returns:
            multi_select_widget (widget): generic multi select widget built from given config
        """
        options, default = self.get_multi_select_options(config)

        if not options:
            return

        multi_select_label = config.get(c.MULTI_SELECT_LABEL_KEY, "")
        multi_select_name = config.get(c.MULTI_SELECT_DISPLAY_NAME_KEY, "")

        multi_select_widget = pn.widgets.MultiSelect(
            options=options,
            value=default,
            size=min(len(options), 5),
            name=multi_select_name,
        )

        multi_select_widget.params = {
            "label": multi_select_label,
            "reset_to": default,
        }
        return multi_select_widget

    def create(self, config: dict[str, Any]) -> pn.widgets.MultiSelect | None:
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
        multi_select_register_value = config.get(c.MULTI_SELECT_REGISTER_AS_KEY)
        registered_multi_select_widget = {
            "item_filter": ItemFilterWidget,
            "upper_item_filter": UpperItemFilterWidget,
            "reco_filter": RecoFilterWidget,
            "model_choice": ModelChoiceWidget,
        }.get(multi_select_register_value, None)

        if registered_multi_select_widget:
            multi_select_widget = registered_multi_select_widget(self.reco_explorer_app_instance, self.controller_instance).create(config)
        else:
            multi_select_widget = self.build_multi_select_widget(config)

        if multi_select_widget is not None:
            multi_select_widget.is_leaf_widget = True

        self.set_action_parameter(config, multi_select_widget)
        return multi_select_widget

    def set_action_parameter(self, config: dict[str, Any], multi_select_widget: pn.widgets.MultiSelect) -> pn.widgets.MultiSelect | None:
        """
        Sets action option parameter on the multi-select widget based on the provided configuration. Action parameter will be used to toggle
        visibility of other widgets by selecting the configured option. Action parameter are dictionary entries with key = multi select
        option value and value = label of the target widget.

        :param config: Configuration containing trigger actions.
        :param multi_select_widget: The multi-select widget to set action parameter on.
        :return: The multi select widget with the action parameter attached if configured
        """
        if config.get(c.MULTI_SELECT_ACTION_OPTION_KEY):
            action_parameter = {list(pair.keys())[0]: list(pair.values())[0] for pair in config.get(c.MULTI_SELECT_ACTION_OPTION_KEY)}
            if action_parameter:
                multi_select_widget.action_parameter = action_parameter
        return multi_select_widget

    def trigger_multi_select_reco_filter_choice(self, event):
        """
        Checks multi select widget for action parameters and sets visibility trigger for each of them.
        After that runs the usual get items function to search for items with given filters and parameters.

        :param event: The event which triggers the watcher function. Contains the widget itself.
        :return:
        """
        if hasattr(event.obj, "action_parameter"):
            for action_option_value, action_target_widget_label in event.obj.action_parameter.items():
                action_target_widget = self.find_widget_by_name_recursive(
                    self.reco_explorer_app_instance.config_based_nav_controls,
                    action_target_widget_label
                )
                if action_target_widget:
                    action_target_widget.visible = action_option_value == event.new[0]

        self.reco_explorer_app_instance.get_items_with_parameters()

    def find_widget_by_name_recursive(self, widget, target_name):
        """
        Gets a widget from a widget group (for example panels widgets box) and search it by given name (label).
        Calls itself for nested widgets (recursive).

        :param widget: Widget that is the source for the search.
        :param target_name: Name of the target widget.
        :return: The widget if found or None if no widget is found.
        """
        if hasattr(widget, "name") and widget.name == target_name:
            return widget

        if hasattr(widget, "objects"):
            for obj in widget.objects:
                found_widget = self.find_widget_by_name_recursive(obj, target_name)
                if found_widget is not None:
                    return found_widget

        return None


class ItemFilterWidget(MultiSelectionWidget):
    def create(self, config: dict[str, Any]) -> pn.widgets.MultiSelect | None:
        """
        Builds a multi select item filter widget based on the given config from config yaml.
        An item filter is a standard multi select widget which gets registered as item filter at the controller.

        Args:
            multi_select_config (config): config of a multi select from config yaml.

        Returns:
            multi_select_widget (widget): final item filter widget built from given config
        """
        item_filter_widget = self.build_multi_select_widget(config)

        if not item_filter_widget:
            return

        item_filter_widget.param.watch(
            self.reco_explorer_app_instance.trigger_item_filter_choice,
            "value",
            onlychanged=True,
        )
        self.controller_instance.register("item_filter", item_filter_widget)

        item_filter_widget.reset_identifier = c.RESET_IDENTIFIER_ITEM_FILTER

        return item_filter_widget


class ModelChoiceWidget(MultiSelectionWidget):
    def create(self, config: dict[str, Any]) -> pn.widgets.MultiSelect | None:
        """
        Builds a multi select model choice widget based on the given config from config yaml.
        A model choice widget is a standard multi select widget which gets registered as model_choice at the controller.

        Args:
            multi_select_config (config): config of a multi select from config yaml.

        Returns:
            multi_select_widget (widget): final model choice multi select widget built from given config
        """
        model_choice_widget = self.build_multi_select_widget(config)

        if not model_choice_widget:
            return

        model_watcher = model_choice_widget.param.watch(
            self.reco_explorer_app_instance.trigger_model_choice_new,
            "value",
            onlychanged=True,
        )
        self.controller_instance.register(
            "model_choice",
            model_choice_widget,
            model_watcher,
            self.reco_explorer_app_instance.trigger_model_choice_new,
        )

        model_choice_widget.reset_identifier = c.RESET_IDENTIFIER_MODEL_CHOICE

        return model_choice_widget


class RecoFilterWidget(MultiSelectionWidget):
    def create(self, config: dict[str, Any]) -> pn.widgets.MultiSelect | None:
        """
        Builds a multi select recommendation filter widget based on the given config from config yaml.
        A recommendation filter is a standard multi select widget which gets registered as reco filter at the controller.
        This function also sets up visible actions for the multi select, which get added to the widget (if configured).

        Args:
            multi_select_config (config): config of a multi select from config yaml.

        Returns:
            multi_select_widget (widget): final item filter widget built from given config
        """
        reco_filter_widget = self.build_multi_select_widget(config)
        reco_filter_label = config.get(c.MULTI_SELECT_LABEL_KEY)

        if (reco_filter_widget is None) or not reco_filter_label:
            return

        reco_filter_widget.params = {"label": reco_filter_label, "reset_to": []}

        reco_filter_watcher = reco_filter_widget.param.watch(
            self.trigger_multi_select_reco_filter_choice,
            "value",
            onlychanged=True,
        )
        self.controller_instance.register(
            "reco_filter",
            reco_filter_widget,
            reco_filter_watcher,
            self.trigger_multi_select_reco_filter_choice,
        )

        reco_filter_widget.reset_identifier = c.RESET_IDENTIFIER_RECO_FILTER

        return reco_filter_widget


class UpperItemFilterWidget(MultiSelectionWidget):
    def create(self, config) -> pn.widgets.MultiSelect | None:
        """
        Builds a multi select upper filter widget based on the given config from config yaml.
        An upper item filter is a  multi select widget which gets registered as upper item filter at the controller.
        It also is linked to an item filter by name reference and needs a filter category to work.

        Args:
            multi_select_config (config): config of a multi select from config yaml.

        Returns:
            multi_select_widget (widget): final upper item filter widget built from given config
        """
        upper_item_filter_widget = self.build_multi_select_widget(config)
        linked_filter_name = config.get(c.MULTI_SELECT_LINKED_FILTER_NAME_KEY)
        filter_category = config.get(c.MULTI_SELECT_FILTER_CATEGORY)

        if (
            (upper_item_filter_widget is None)
            or (not linked_filter_name)
            or (not filter_category)
        ):
            return

        upper_item_filter_widget.param.watch(
            lambda event: self.load_options_after_filter_got_set(
                linked_filter_name, filter_category, upper_item_filter_widget, event
            ),
            "value",
            onlychanged=True,
        )
        self.controller_instance.register("upper_item_filter", upper_item_filter_widget)

        upper_item_filter_widget.reset_identifier = c.RESET_IDENTIFIER_UPPER_ITEM_FILTER

        return upper_item_filter_widget

    def load_options_after_filter_got_set(
        self, target_widget_name, category, filter_widget, event
    ):
        """
        Loads options for item filter after upper item filter was triggered. First select the referenced item filter by name
        and then get and insert new filter options for the target item filter based on the selected upper item filter.

        :param target_widget_name: target item filter widgets name.
        :param category: category to set how to get new option values for target item filter.
        :param filter_widget: upper item filter widget.
        :param event: event type triggered by upper item filter.
        """
        if (event.type != "changed") or (category != "genres"):
            return

        target_widget = self.find_widget_by_name_recursive(
            self.reco_explorer_app_instance.config_based_nav_controls,
            target_widget_name,
        )

        target_widget.value = (
            self.controller_instance.get_genres_and_subgenres_from_upper_category(
                filter_widget.value, category
            )
        )
