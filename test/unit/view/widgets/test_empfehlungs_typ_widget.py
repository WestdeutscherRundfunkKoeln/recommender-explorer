from unittest.mock import MagicMock
from src.view.widgets.empfehlungstyp_widget import EmpfehlungstypWidget  # Replace with the actual module path
import panel as pn
import pytest


@pytest.fixture
def widget():
    # Mock instances for testing
    reco_explorer_app_instance = None  # Replace with a mock if necessary
    controller_instance = None  # Replace with a mock if necessary
    widget = EmpfehlungstypWidget(reco_explorer_app_instance, controller_instance)
    return widget


def test_radioboxgroup_structure(widget):
    # Create the widget
    pn_row = widget.create()

    # Access the column (first child in the Row)
    column = pn_row[0]
    assert isinstance(column, pn.Column), "First item should be a Column."
    assert column.width == 285, "Column width should be 285."

    # Access the Accordion
    accordion = column[0]
    assert isinstance(accordion, pn.layout.Accordion), "First item in the column should be an Accordion."

    # Access the RadioBoxGroup
    radio_box_group = accordion[0][0]
    assert isinstance(radio_box_group, pn.widgets.RadioBoxGroup), "First item in the inner column should be a RadioBoxGroup."

    # Check the default value of the RadioBoxGroup
    assert radio_box_group.value == "Ähnlichkeit", f"Expected 'Diversität', but got {radio_box_group.value}."


def test_tooltip_existence(widget):
    # Create the widget
    pn_row = widget.create()

    # Access the TooltipIcon (second child in the Row)
    tooltip = pn_row[1]
    assert isinstance(tooltip, pn.widgets.TooltipIcon), "Second item in the Row should be a TooltipIcon."
    assert tooltip.value.startswith("Sie können zwischen"), "Tooltip text should start with 'Sie können zwischen'."


def test_button_count(widget):
    # Create the widget
    pn_row = widget.create()

    # Access the Accordion and inner Column
    column = pn_row[0]
    accordion = column[0]
    row_btn = accordion[0][1]
    assert isinstance(row_btn, pn.Row), "Second item in the inner column should be a Row."

    # Check the number of buttons in the row
    assert len(row_btn.objects) == 2, "There should be 2 buttons in the row initially."


def test_button_label_change_on_radiobox(widget):
    # Create the widget
    pn_row = widget.create()

    # Access the Accordion, RadioBoxGroup, and Button Row
    column = pn_row[0]
    accordion = column[0]
    radio_box_group = accordion[0][0]
    row_btn = accordion[0][1]

    # Simulate changing the radio box value to 'Diversität'
    radio_box_group.value = 'Diversität'

    # Check if the correct buttons are displayed
    assert len(row_btn.objects) == 2, "There should be 2 buttons for 'Diversität'."
    assert row_btn[0].name == "Weniger Diversität", "First button should be 'Weniger Diversität'."
    assert row_btn[1].name == "Mehr Diversität", "Second button should be 'Mehr Diversität'."

    # Simulate changing the radio box value to 'Aktualität'
    radio_box_group.value = 'Aktualität'

    # Check if the correct buttons are displayed
    assert len(row_btn.objects) == 2, "There should be 2 buttons for 'Aktualität'."
    assert row_btn[0].name == "Weniger Aktualität", "First button should be 'Weniger Aktualität'."
    assert row_btn[1].name == "Mehr Aktualität", "Second button should be 'Mehr Aktualität'."

