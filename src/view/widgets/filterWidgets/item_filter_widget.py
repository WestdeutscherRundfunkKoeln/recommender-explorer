class ItemFilterWidget:
    def __init__(
        self,
        multi_select_widget_instance,
        reco_explorer_app_instance,
        controller_instance,
    ):
        self.multi_select_widget_instance = multi_select_widget_instance
        self.reco_explorer_app_instance = reco_explorer_app_instance
        self.controller_instance = controller_instance

    def create_item_filter_multi_select(self, multi_select_config):
        """
        Builds a multi select item filter widget based on the given config from config yaml.
        An item filter is a standard multi select widget which gets registered as item filter at the controller.

        Args:
            multi_select_config (config): config of a multi select from config yaml.

        Returns:
            multi_select_widget (widget): final item filter widget built from given config
        """
        item_filter_widget = (
            self.multi_select_widget_instance.build_multi_select_widget(
                multi_select_config
            )
        )
        if item_filter_widget:
            item_filter_widget.param.watch(
                self.reco_explorer_app_instance.trigger_item_filter_choice,
                "value",
                onlychanged=True,
            )
            self.controller_instance.register("item_filter", item_filter_widget)
            return item_filter_widget
        else:
            return None
