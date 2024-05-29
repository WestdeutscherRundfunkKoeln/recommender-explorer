from typing import TYPE_CHECKING, Any
from abc import ABC, abstractmethod
from panel.widgets import Widget
from panel.layout import Panel

if TYPE_CHECKING:
    from controller.reco_controller import RecommendationController
    from view.RecoExplorerApp import RecoExplorerApp
    from view.widgets.multi_select_widget import MultiSelectionWidget


class UIWidget(ABC):
    def __init__(
        self,
        reco_explorer_app_instance: "RecoExplorerApp",
        controller_instance: "RecommendationController",
    ) -> None:
        self.reco_explorer_app_instance = reco_explorer_app_instance
        self.controller_instance = controller_instance

    @abstractmethod
    def create(self, config: dict[str, Any]) -> Widget | Panel | None:
        pass


class FilterWidget(UIWidget):
    def __init__(
        self,
        multi_select_widget_instance: "MultiSelectionWidget",
        reco_explorer_app_instance: "RecoExplorerApp",
        controller_instance: "RecommendationController",
    ):
        self.multi_select_widget_instance = multi_select_widget_instance
        super().__init__(reco_explorer_app_instance, controller_instance)
