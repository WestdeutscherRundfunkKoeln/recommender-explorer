import panel as pn
from view.widgets.widget import UIWidget
from view.util.view_utils import collect_leaf_widgets


from .. import ui_constants as c


class ResetButtonWidget(UIWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout_widget_types = (
            pn.layout.accordion.Accordion,
            pn.layout.base.Column,
        )

    def create(self, block) -> pn.widgets.Button:
        reset_button_widget = pn.widgets.Button(
            name=c.RESET_BUTTON_LABEL,
            margin=10,
            button_type="primary",
        )

        widgets_to_reset = self.get_widgets_to_reset(block)
        reset_button_widget = self.set_reset_button_params(
            reset_button_widget, widgets_to_reset
        )

        async def _reset_block_contents(event):
            await self.reset_block_contents(event, widgets_to_reset)

        reset_button_widget.on_click(_reset_block_contents)

        return reset_button_widget

    def set_reset_button_params(
        self, reset_button_widget, widgets_to_reset
    ) -> pn.widgets.Button:
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
            "resets": list_of_reset_identifiers,
        }
        return reset_button_widget

    async def reset_block_contents(self, event, block):
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
            component_label = widget.params.get("label","")
            component_group = event.obj.params["resets"]
            self.controller_instance.reset_component(component_group, component_label)

        self.controller_instance.reset_page_number()

        reset_identifiers_item = [
            c.RESET_IDENTIFIER_MODEL_CHOICE,
            c.RESET_IDENTIFIER_ITEM_CHOICE,
            c.RESET_IDENTIFIER_UPPER_ITEM_FILTER,
            c.RESET_IDENTIFIER_ITEM_FILTER,
        ]

        reset_identifiers_reco = [
            c.RESET_IDENTIFIER_RECO_FILTER,
            c.RESET_IDENTIFIER_UPPER_RECO_FILTER,
        ]

        for reset_type in event.obj.params["resets"]:
            if reset_type in reset_identifiers_item:
                self.reco_explorer_app_instance.main_content[:] = []
                self.reco_explorer_app_instance.draw_pagination()
            elif reset_type in reset_identifiers_reco:
                await self.reco_explorer_app_instance.get_items_with_parameters()

    def get_widgets_to_reset(self, block):
        """
        Get the list of widgets to reset for a given block.

        :param block: The block from which to collect the widgets.
        :return: The list of widgets to reset.
        """
        widgets_to_reset = []
        for widget in block:
            widgets_to_reset.extend(
                collect_leaf_widgets(widget, self.layout_widget_types)
            )
        return widgets_to_reset
