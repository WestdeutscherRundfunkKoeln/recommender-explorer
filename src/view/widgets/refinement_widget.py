import panel as pn
from view.widgets.widget import UIWidget
from view import ui_constants as c

#Refeinement widget
REFINEMENT_WIDGET_TYPE_VALUE = "refinement_widget"
REFINEMENT_WIDGET_TOOLTIP = "Sie können zwischen verschiedenen Arten der Empfehlungsgenerierung für einen bestimmten Artikel wechseln und die Dimension des jeweiligen Typs verstärken."
REFINEMENT_WIDGET_ACCORDION_LABEL = "Empfehlungs-Typ"
REFINEMENT_WIDGET_ALERT = "<b> Die Ergebnisse können nicht weiter geändert werden! ⚠️ </b>"
DIVERSITY = "Diversität"
RECENCY = "Aktualität"

class RefinementWidget(pn.Column, UIWidget):

    def __init__(self, reco_explorer_app_instance, controller_instance):
        # Initialize parent classes
        pn.Column.__init__(self)
        UIWidget.__init__(self, reco_explorer_app_instance, controller_instance)

    def create(self) -> pn.Column:
        """
        Create and return a panel containing the radio buttons and corresponding buttons for the selected option.
        """
        # Create radio buttons
        self.radio_box_group = pn.widgets.RadioBoxGroup(
            #options=['Ähnlichkeit', 'Diversität', 'Aktualität'],
            options=['Ähnlichkeit'],
            value='Ähnlichkeit',  # Default value
            name='refinement_widget',
        )

        # Store a reference to the current widget in the radio_box_group
        self.radio_box_group.widget_instance = self

        self.radio_box_group.params = {
            "label": 'refinementType',  # must always be named like this to avoid errors in other parts of the code.
            "reset_to": 'Ähnlichkeit',
            "direction": "",
            "switch_weights" : False
        }

        # Watch the value change
        radio_box_group_watcher = self.radio_box_group.param.watch(self.update_buttons, 'value', onlychanged=True, )

        # Register the widget with the controller
        self.controller_instance.register(
            "reco_filter",
            self.radio_box_group,
            radio_box_group_watcher,
            self.reco_explorer_app_instance.trigger_reco_filter_choice,
        )

        self.radio_box_group.reset_identifier = c.RESET_IDENTIFIER_RECO_FILTER

        self.radio_box_group.is_leaf_widget = True

        self.btn1 = pn.widgets.Button(name='Ähnlicher', width=120)
        self.btn2 = pn.widgets.Button(name='Aktueller', width=120)

        self.btn1.on_click(self.button_clicked)
        self.btn2.on_click(self.button_clicked)

        self.tooltip_widget = pn.widgets.TooltipIcon(value=REFINEMENT_WIDGET_TOOLTIP)

        # Create an alert when the button is disabled
        self.alert = pn.pane.Alert(REFINEMENT_WIDGET_ALERT,
                                   alert_type="light",
                                   styles={"font-size": "11px", "padding_top": "0px", "padding_bottom": "0px"
                                       , "text-align": "center"}, visible=False, )

        # Create the accordion layout
        self.accordion = pn.layout.Accordion()
        self.accordion_with_width = pn.Column(self.accordion, width=285)
        self.accordion.active = [0]

        # The main column to be added into the accordion
        self.col = pn.Column()

        # The row that holds the buttons "Ähnlichkeit buttons by default"
        self.row_btn = pn.Row()



        self.col.append(self.radio_box_group)
        self.row_btn.append(self.btn1)
        self.row_btn.append(self.btn2)

        # Add the row of buttons to the main column
        self.col.append(self.row_btn)
        self.col.append(self.alert)  # Add the alert to the UI but keep it hidden
        # Add the main column to the accordion
        self.accordion.append((REFINEMENT_WIDGET_ACCORDION_LABEL, self.col))

        return pn.Row(self.accordion_with_width,self.tooltip_widget)

    async def update_buttons(self, event):
        """
        Updates the buttons based on the selected radio option.
        """
        label_map = {
            DIVERSITY: ("Weniger Diversität", "Mehr Diversität"),
            RECENCY: ("Weniger Aktualität", "Mehr Aktualität")
        }

        self.btn1.name, self.btn2.name = label_map.get(
            event.new,
            ("Ähnlicher", "Aktueller")
        )

        # reset the direction
        self.radio_box_group.params["direction"] = ""
        self.radio_box_group.params = {
            "label": 'refinementType',
            "reset_to": 'Ähnlichkeit',
            "direction": "",
        }

        #hide the alert if visible
        self.alert.visible = False

        # Await the async call
        await self.reco_explorer_app_instance.trigger_item_selection(event)

    async def button_clicked(self, event):
        self.radio_box_group.params["direction"] = event.obj.name

        await self.reco_explorer_app_instance.trigger_item_selection(event)

        self.radio_box_group.params["direction"] = ""

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
