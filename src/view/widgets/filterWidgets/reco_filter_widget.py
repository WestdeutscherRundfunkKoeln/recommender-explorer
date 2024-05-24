from ... import ui_constants as c


class RecoFilterWidget:
    def __init__(
        self,
        multi_select_widget_instance,
        reco_explorer_app_instance,
        controller_instance,
    ):
        self.multi_select_widget_instance = multi_select_widget_instance
        self.reco_explorer_app_instance = reco_explorer_app_instance
        self.controller_instance = controller_instance

    def create_reco_filter_multi_select(self, multi_select_config):
        """
        Builds a multi select recommendation filter widget based on the given config from config yaml.
        A recommendation filter is a standard multi select widget which gets registered as reco filter at the controller.
        This function also sets up visible actions for the multi select, which get added to the widget (if configured).

        Args:
            multi_select_config (config): config of a multi select from config yaml.

        Returns:
            multi_select_widget (widget): final item filter widget built from given config
        """
        reco_filter_widget = (
            self.multi_select_widget_instance.build_multi_select_widget(
                multi_select_config
            )
        )
        reco_filter_label = multi_select_config.get(c.MULTI_SELECT_LABEL_KEY)
        action_list = []
        action_2_list = []
        if multi_select_config.get("visible_action"):
            for action_1 in multi_select_config.get("visible_action"):
                action_list.append(action_1.get("action_name"))
        if multi_select_config.get("visible_action_2"):
            for action_2 in multi_select_config.get("visible_action_2"):
                action_2_list.append(action_2.get("action_name"))
        if reco_filter_widget and reco_filter_label:
            reco_filter_widget = self.set_params_for_reco_filter(
                reco_filter_widget, reco_filter_label, action_list, action_2_list
            )

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
        else:
            return None

    def set_params_for_reco_filter(
        self, reco_filter_widget, reco_filter_label, action_list, action_2_list
    ):
        """
        Sets params at multi select widgets based on given parameters.

        :param reco_filter_widget: The multi select widget
        :param reco_filter_label: The label for the widget
        :param action_list: List of visible actions for the multi select widget
        :param action_2_list: List 2 of visible actions for the multi select widget
        :return: Multi Select widget with params
        """
        if len(action_list) > 0 and len(action_2_list) > 0:
            reco_filter_widget.params = {
                "label": reco_filter_label,
                "visible_action": tuple(action_list),
                "visible_action_2": tuple(action_2_list),
                "reset_to": [],
            }
        elif len(action_list) > 0:
            reco_filter_widget.params = {
                "label": reco_filter_label,
                "visible_action": tuple(action_list),
                "reset_to": [],
            }
        else:
            reco_filter_widget.params = {"label": reco_filter_label, "reset_to": []}
        return reco_filter_widget
