from ... import ui_constants as c


class UpperItemFilterWidget:
    def __init__(
        self,
        multi_select_widget_instance,
        reco_explorer_app_instance,
        controller_instance,
    ):
        self.multi_select_widget_instance = multi_select_widget_instance
        self.reco_explorer_app_instance = reco_explorer_app_instance
        self.controller_instance = controller_instance

    def create_upper_item_filter_multi_select(self, multi_select_config):
        """
        Builds a multi select upper filter widget based on the given config from config yaml.
        An upper item filter is a  multi select widget which gets registered as upper item filter at the controller.
        It also is linked to an item filter by name reference and needs a filter category to work.

        Args:
            multi_select_config (config): config of a multi select from config yaml.

        Returns:
            multi_select_widget (widget): final upper item filter widget built from given config
        """
        upper_item_filter_widget = (
            self.multi_select_widget_instance.build_multi_select_widget(
                multi_select_config
            )
        )
        linked_filter_name = multi_select_config.get(
            c.MULTI_SELECT_LINKED_FILTER_NAME_KEY
        )
        filter_category = multi_select_config.get(c.MULTI_SELECT_FILTER_CATEGORY)
        if upper_item_filter_widget and linked_filter_name and filter_category:
            upper_item_filter_widget.param.watch(
                lambda event: self.controller_instance.load_options_after_filter_got_set(
                    linked_filter_name, filter_category, upper_item_filter_widget, event
                ),
                "value",
                onlychanged=True,
            )
            self.controller_instance.register(
                "upper_item_filter", upper_item_filter_widget
            )
            return upper_item_filter_widget
        else:
            return None

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
        upper_category_widget = filter_widget
        target_widget = self.find_widget_by_name_recursive(
            self.reco_explorer_app_instance.config_based_nav_controls,
            target_widget_name,
        )
        if event.type == "changed":
            if category == "genres":
                target_widget.value = self.controller_instance.get_genres_and_subgenres_from_upper_category(
                    upper_category_widget.value, category
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
