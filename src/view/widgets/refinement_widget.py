import panel as pn
from view.widgets.widget import UIWidget
from view import ui_constants as c


class RefinementWidget(pn.Column, UIWidget):

    def __init__(self, reco_explorer_app_instance, controller_instance):
        # Initialize parent classes
        pn.Column.__init__(self)
        UIWidget.__init__(self, reco_explorer_app_instance, controller_instance)
        self.loading_spinner = pn.indicators.LoadingSpinner(value=False, width=30, height=30, visible=True)

        # Create radio buttons
        self.radio_box_group = pn.widgets.RadioBoxGroup(
            options=['Ähnlichkeit', 'Diversität', 'Aktualität'],
            value='Ähnlichkeit',  # Default value
            name = 'refinement_widget',
        )

        # Store a reference to the current widget in the radio_box_group
        self.radio_box_group._widget_instance = self

        self.radio_box_group.params = {
            "label": 'refinementType', # must always be named like this to avoid errors in other parts of the code.
            "reset_to": 'Ähnlichkeit',
            "direction": ""
        }

        # Watch the value change
        radio_box_group_watcher = self.radio_box_group.param.watch(self.update_buttons, 'value', onlychanged=True,)
        # Register the widget with the controller
        self.controller_instance.register(
            "reco_filter",
            self.radio_box_group,
            radio_box_group_watcher,
            self.reco_explorer_app_instance.trigger_reco_filter_choice,
        )

        self.radio_box_group.reset_identifier = c.RESET_IDENTIFIER_ITEM_FILTER

        self.radio_box_group.is_leaf_widget = True


        self.btn1 = pn.widgets.Button(name='Ähnlicher', width=120)
        self.btn2 = pn.widgets.Button(name='Aktueller', width=120)

        self.btn1.on_click(self.button_clicked)
        self.btn2.on_click(self.button_clicked)

        self.tooltip_widget = pn.widgets.TooltipIcon(value=c.REFINEMENT_WIDGET_TOOLTIP)

        # Create an alert when the button is disabled
        self.alert = pn.pane.Alert("<b> Die Ergebnisse können nicht weiter geändert werden! ⚠️ </b>",
        alert_type="light", styles={"font-size": "11px", "padding_top": "0px","padding_bottom": "0px"
        ,"text-align": "center"},visible=False,)

        # Create the accordion layout
        self.accordion = pn.layout.Accordion()
        self.accordion_with_width = pn.Column(self.accordion, width=285)

        # The main column to be added into the accordion
        self.col = pn.Column()

        # The row that holds the buttons "Ähnlichkeit buttons by default"
        self.row_btn = pn.Row()

    def create(self) -> pn.Column:
        """
        Create and return a panel containing the radio buttons and corresponding buttons for the selected option.
        """
        self.col.append(self.radio_box_group)
        self.row_btn.append(self.btn1)
        self.row_btn.append(self.btn2)
        self.row_btn.append(self.loading_spinner)

        # Add the row of buttons to the main column
        self.col.append(self.row_btn)
        self.col.append(self.alert)  # Add the alert to the UI but keep it hidden
        # Add the main column to the accordion
        self.accordion.append((c.REFINEMENT_WIDGET_ACCORDION_LABEL, self.col))

        return pn.Row(self.accordion_with_width,self.tooltip_widget)


    async def update_buttons(self, event):
        """
        Updates the buttons based on the selected radio option.
        """

        self.loading_spinner.value = True

        if event.new == 'Diversität':
            self.btn1.name = "Weniger Diversität"
            self.btn2.name = "Mehr Diversität"
        elif event.new == 'Aktualität':
            self.btn1.name = "Weniger Aktualität"
            self.btn2.name = "Mehr Aktualität"
        else:
            self.btn1.name = "Ähnlicher"
            self.btn2.name = "Aktueller"

         # reset the direction
        self.radio_box_group.params = {
            "direction": '',
            "label": 'refinementType',
            "reset_to": 'Ähnlichkeit',
        }

        #hide the alert if visible
        self.alert.visible = False

        # Await the async call
        await self.reco_explorer_app_instance.trigger_item_selection(event)

        self.loading_spinner.value = False

    async def button_clicked(self, event):
        self.loading_spinner.value = True

        self.radio_box_group.params = {
            "direction": event.obj.name,
            "label": 'refinementType',
            "reset_to": 'Ähnlichkeit',
        }

        # Await the async call
        await self.reco_explorer_app_instance.trigger_item_selection(event)

        self.loading_spinner.value = False

    def disable_active_button(self):
        """Disable the active button based on the selected radio option."""
        selected_type = self.radio_box_group.value
        direction = self.radio_box_group.params["direction"]

        button_map = {
            "Ähnlichkeit": {"Ähnlicher": self.btn1, "Aktueller": self.btn2},
            "Aktualität": {"Weniger Aktualität": self.btn1, "Mehr Aktualität": self.btn2},
            "Diversität": {"Weniger Diversität": self.btn1, "Mehr Diversität": self.btn2},
        }

        if selected_type in button_map and direction in button_map[selected_type]:
            button_to_disable = button_map[selected_type][direction]
            button_to_disable.disabled = not button_to_disable.disabled
            print(f"Disabled button: {direction}")
            self.alert.visible = not self.alert.visible  # Show the alert

    def enable_all_buttons(self):
        self.btn1.disabled = False
        self.btn2.disabled = False
        self.alert.visible = False
