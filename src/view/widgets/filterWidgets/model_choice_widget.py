class ModelChoiceWidget:

    def __init__(self, multi_select_widget_instance, reco_explorer_app_instance, controller_instance):
        self.multi_select_widget_instance = multi_select_widget_instance
        self.reco_explorer_app_instance = reco_explorer_app_instance
        self.controller_instance = controller_instance

    def create_model_choice_multi_select(self, multi_select_config):
        """
        Builds a multi select model choice widget based on the given config from config yaml.
        A model choice widget is a standard multi select widget which gets registered as model_choice at the controller.

        Args:
            multi_select_config (config): config of a multi select from config yaml.

        Returns:
            multi_select_widget (widget): final model choice multi select widget built from given config
        """
        model_choice_widget = self.multi_select_widget_instance.build_multi_select_widget(multi_select_config)
        if model_choice_widget:
            model_watcher = model_choice_widget.param.watch(self.reco_explorer_app_instance.trigger_model_choice_new, 'value', onlychanged=True)
            self.controller_instance.register('model_choice', model_choice_widget, model_watcher, self.reco_explorer_app_instance.trigger_model_choice_new)
            return model_choice_widget
        return None
