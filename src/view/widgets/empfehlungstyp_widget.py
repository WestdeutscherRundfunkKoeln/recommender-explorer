import panel as pn
from view.widgets.widget import UIWidget
from view import ui_constants as c





class EmpfehlungstypWidget(pn.Column, UIWidget):

    def __init__(self, reco_explorer_app_instance, controller_instance):
        # Initialize parent classes
        pn.Column.__init__(self)
        UIWidget.__init__(self, reco_explorer_app_instance, controller_instance)


    def create(self) -> pn.Column:
        """
        Create and return a panel containing the radio buttons and corresponding buttons for the selected option.
        """

        # Create radio buttons (this will be the same each time)
        self.radio_box_group = pn.widgets.RadioBoxGroup(
            options=['Ähnlichkeit', 'Diversität', 'Aktualität'],
            value='Ähnlichkeit',  # Default value as a list,
            name = 'empfehlungstyp',
        )

        self.radio_box_group.params = {
            "label": 'empfehlungstyp',
            "reset_to": 'Ähnlichkeit',
            "direction": ""
        }

        # Watch the value change
        radio_box_group_watcher = self.radio_box_group.param.watch(self.update_buttons, 'value', onlychanged=True,)
        # Register the widget with the controller
        self.controller_instance.register(
            "item_filter",
            self.radio_box_group,
            radio_box_group_watcher,
            self.reco_explorer_app_instance.trigger_reco_filter_choice,
        )

        self.radio_box_group.reset_identifier = c.RESET_IDENTIFIER_RECO_FILTER

        self.radio_box_group.is_leaf_widget = True


        self.btn1 = pn.widgets.Button(name='Ähnlicher', width=120)
        self.btn2 = pn.widgets.Button(name='Aktueller', width=120)
        self.btn3 = pn.widgets.Button(name='Weniger Diversität', width=120)
        self.btn4 = pn.widgets.Button(name='Mehr Diversität', width=120)
        self.btn5 = pn.widgets.Button(name='Weniger Aktualität', width=120)
        self.btn6 = pn.widgets.Button(name='Mehr Aktualität', width=120)

        self.btn1.on_click(self.button_clicked)
        self.btn2.on_click(self.button_clicked)
        self.btn3.on_click(self.button_clicked)
        self.btn4.on_click(self.button_clicked)
        self.btn5.on_click(self.button_clicked)
        self.btn6.on_click(self.button_clicked)

        # Create the accordion layout
        self.accordion = pn.layout.Accordion()
        self.accordion_with_width = pn.Column(self.accordion, width=285)


        # The main column to be added into the accordion
        self.col = pn.Column()
        self.col.append(self.radio_box_group)

        # The row that holds the buttons "Ähnlichkeit buttons by default"
        self.row_btn = pn.Row()
        self.row_btn.append(self.btn1)
        self.row_btn.append(self.btn2)

        tooltip_widget = pn.widgets.TooltipIcon(value="Sie können zwischen verschiedenen Arten der Empfehlungsgenerierung für einen bestimmten Artikel wechseln und die Dimension des jeweiligen Typs verstärken.")

        # Add the row of buttons to the main column
        self.col.append(self.row_btn)
        # Add the main column to the accordion
        self.accordion.append(('Empfehlungs-Typ', self.col))

        return pn.Row(self.accordion_with_width,tooltip_widget)


    async def update_buttons(self, event):
        """
        Updates the visible buttons based on the selected radio option.
        """
        # Clear the old buttons
        self.row_btn.clear()
        if event.new == 'Diversität':
            self.row_btn.append(self.btn3)
            self.row_btn.append(self.btn4)
        elif event.new == 'Aktualität':
            self.row_btn.append(self.btn5)
            self.row_btn.append(self.btn6)
        else:
            self.row_btn.append(self.btn1)
            self.row_btn.append(self.btn2)

         # reset the direction
        self.radio_box_group.params = {
            "direction": '',
            "label": 'empfehlungstyp',
            "reset_to": 'Ähnlichkeit',
        }

        # Await the async call
        await self.reco_explorer_app_instance.trigger_item_selection(event)


    async def button_clicked(self, event):
        self.radio_box_group.params = {
            "direction": event.obj.name,
            "label": 'empfehlungstyp',
            "reset_to": 'Ähnlichkeit',
        }
        print(self.radio_box_group.params)

        # Await the async call
        await self.reco_explorer_app_instance.trigger_item_selection(event)


