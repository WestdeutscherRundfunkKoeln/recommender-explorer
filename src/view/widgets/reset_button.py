from typing import Any
import panel as pn
from view.widgets.widget import UIWidget
from .. import ui_constants as c


class ResetButtonWidget(UIWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout_widget_types = (
            pn.layout.accordion.Accordion,
            pn.layout.base.Column
        )

    def create(self, block) -> pn.widgets.Button:
        reset_button_widget = pn.widgets.Button(
            name=c.RESET_BUTTON_LABEL,
            button_type='primary',
            margin=10
        )

        widgets_to_reset = self.get_widgets_to_reset(block)
        reset_button_widget = self.set_reset_button_params(reset_button_widget, widgets_to_reset)
        reset_button_widget.on_click(lambda event: self.reset_block_contents(event, widgets_to_reset))

        return reset_button_widget

    def set_reset_button_params(self, reset_button_widget, widgets_to_reset) -> pn.widgets.Button:
        """
        Set the parameters for the reset button widget.

        :param reset_button_widget: The reset button widget to set the parameters for.
        :param widgets_to_reset: A list of widgets to reset when the button is clicked.
        :return: The reset button widget with the updated parameters.
        """
        list_of_reset_identifiers = []
        for widget in widgets_to_reset:
            list_of_reset_identifiers.append(widget.reset_identifier)
        list_of_reset_identifiers = list(set(list_of_reset_identifiers))
        reset_button_widget.params = {
            "label": "resetter",
            "resets": list_of_reset_identifiers
        }
        return reset_button_widget

    def reset_block_contents(self, event, block):
        """
        Resets the contents of the given block by setting the value of
        each widget to its specified reset value. Additionally, resets
        certain identifiers and page number in the controller and updates
        the item grid and floating elements in the reco explorer app if needed.

        :param event: The event that triggered the reset
        :param block: The block containing the widgets to be reset
        :return: None
        """
        for widget in block:
            widget.value = widget.params.get("reset_to")

        self.controller_instance.reset_defaults(event.obj.params["resets"])
        self.controller_instance.reset_page_number()

        reset_identifiers_item = [
            c.RESET_IDENTIFIER_MODEL_CHOICE,
            c.RESET_IDENTIFIER_ITEM_CHOICE,
            c.RESET_IDENTIFIER_UPPER_ITEM_FILTER,
            c.RESET_IDENTIFIER_ITEM_FILTER
        ]

        reset_identifiers_reco = [
            c.RESET_IDENTIFIER_RECO_FILTER,
            c.RESET_IDENTIFIER_UPPER_RECO_FILTER
        ]

        for reset_type in event.obj.params["resets"]:
            if reset_type in reset_identifiers_item:
                self.reco_explorer_app_instance.item_grid.objects = {}
                self.reco_explorer_app_instance.floating_elements.objects = []
                self.reco_explorer_app_instance.draw_pagination()
            elif reset_type in reset_identifiers_reco:
                self.reco_explorer_app_instance.get_items_with_parameters()

    def get_widgets_to_reset(self, block):
        """
        Get the list of widgets to reset for a given block.

        :param block: The block from which to collect the widgets.
        :return: The list of widgets to reset.
        """
        widgets_to_reset = []
        for widget in block:
            widgets_to_reset.extend(self.collect_leaf_widgets(widget))
        return widgets_to_reset

    def collect_leaf_widgets(self, widget):
        """
        This method collects leaf widgets from a given widget.

        :param widget: The widget from which to collect leaf widgets.
        :return: A list of leaf widgets.

        The leaf widgets are collected recursively by traversing through the widget hierarchy.
        Leaf widgets are considered to be widgets with the attribute `is_leaf_widget` set to
        `True`. If the widget is an instance of one of the layout widget types specified in
        `layout_widget_types`, the method recursively collects leaf widgets from its children.
        """
        leaf_widgets = []
        is_leaf_widget = (
                hasattr(widget, "is_leaf_widget")
                and widget.is_leaf_widget
        )

        if not is_leaf_widget and isinstance(widget, self.layout_widget_types):
            for child in widget:
                leaf_widgets.extend(self.collect_leaf_widgets(child))
        elif is_leaf_widget and hasattr(widget, "reset_identifier"):
            leaf_widgets.append(widget)
        return leaf_widgets
