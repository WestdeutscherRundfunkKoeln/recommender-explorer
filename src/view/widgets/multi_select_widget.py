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
            return multi_select_config[c.MULTI_SELECT_DICTIONARY_OPTIONS_KEY], []
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

        multi_select_widget = pn.widgets.MultiSelect(
            options=options,
            value=default,
            size=min(len(options), 5),
            name=multi_select_label,
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
        match multi_select_register_value:
            case "item_filter":
                return ItemFilterWidget(
                    self.reco_explorer_app_instance, self.controller_instance
                ).create(config)
            case "upper_item_filter":
                return UpperItemFilterWidget(
                    self.reco_explorer_app_instance, self.controller_instance
                ).create(config)
            case "reco_filter":
                return RecoFilterWidget(
                    self.reco_explorer_app_instance, self.controller_instance
                ).create(config)
            case "model_choice":
                return ModelChoiceWidget(
                    self.reco_explorer_app_instance, self.controller_instance
                ).create(config)
        return self.build_multi_select_widget(config)


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
        action_list = [
            action.get("action_name") for action in config.get("visible_action", [])
        ]
        action_2_list = [
            action.get("action_name") for action in config.get("visible_action_2", [])
        ]

        if (reco_filter_widget is None) or not reco_filter_label:
            return

        reco_filter_widget.params = {"label": reco_filter_label, "reset_to": []}
        if action_list:
            reco_filter_widget.params["visible_action"] = tuple(action_list)
        if action_2_list:
            reco_filter_widget.params["visible_action_2"] = tuple(action_list)

        reco_filter_watcher = reco_filter_widget.param.watch(
            self.reco_explorer_app_instance.trigger_reco_filter_choice,
            "value",
            onlychanged=True,
        )
        self.controller_instance.register(
            "reco_filter",
            reco_filter_widget,
            reco_filter_watcher,
            self.reco_explorer_app_instance.trigger_reco_filter_choice,
        )
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

    def find_widget_by_name_recursive(self, widget, target_name):
        """
        Check if a widget has the target name. Function is recursive and calls itself while iterating over all
        widgets and widgets nested in that widgets.

        :param widget: a panel widget object
        :param target_name: the name to check the widget for
        """
        # Check if the current widget has the target name
        if hasattr(widget, "name") and widget.name == target_name:
            return widget

        # If the current widget has nested widgets, iterate over them
        if hasattr(widget, "objects"):
            for obj in widget.objects:
                # Recursively call the function to search within nested widgets
                found_widget = self.find_widget_by_name_recursive(obj, target_name)
                if found_widget is not None:
                    return found_widget

        return None
