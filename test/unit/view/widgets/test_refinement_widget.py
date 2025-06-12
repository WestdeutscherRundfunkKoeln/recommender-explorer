import pytest
import panel as pn
from view.widgets.refinement_widget import RefinementWidget, DIVERSITY, RECENCY
from unittest.mock import AsyncMock

class MockApp:
     async def trigger_item_selection(self, event): pass
     def trigger_reco_filter_choice(self, *args): pass
class MockController:
    def register(self, *args): pass

@pytest.fixture
def widget():
    return RefinementWidget(reco_explorer_app_instance=MockApp(), controller_instance=MockController()).create()

def get_widget_instance(widget):
    # Get radio group from layout
    radio = widget[0][0][0][0]
    return radio.widget_instance  # Properly attached


def test_widget_initial_state(widget):
    refinement = get_widget_instance(widget)
    radio = refinement.radio_box_group
    assert radio.value == "Verwandte Inhalte"
    assert isinstance(radio, pn.widgets.RadioBoxGroup)
    assert refinement.btn1.name == "Ähnlicher"
    assert refinement.btn2.name == "Aktueller"
@pytest.mark.asyncio
async def test_button_label_update(widget):
    refinement = get_widget_instance(widget)
    await refinement.update_buttons(type('Event', (object,), {'new': DIVERSITY}))
    assert refinement.btn1.name == "Weniger Diversität"
    assert refinement.btn2.name == "Mehr Diversität"

    await refinement.update_buttons(type('Event', (object,), {'new': RECENCY}))
    assert refinement.btn1.name == "Weniger Aktualität"
    assert refinement.btn2.name == "Mehr Aktualität"

    await  refinement.update_buttons(type('Event', (object,), {'new': "Unknown"}))
    assert refinement.btn1.name == "Ähnlicher"
    assert refinement.btn2.name == "Aktueller"

def test_disable_active_button(widget):
    refinement = get_widget_instance(widget)
    refinement.radio_box_group.value = DIVERSITY
    refinement.radio_box_group.params["direction"] = "Mehr Diversität"

    assert not refinement.btn2.disabled
    refinement.disable_active_button()
    assert refinement.btn2.disabled
    assert refinement.alert.visible

def test_enable_all_buttons(widget):
    refinement = get_widget_instance(widget)
    refinement.btn1.disabled = True
    refinement.btn2.disabled = True
    refinement.alert.visible = True

    refinement.enable_all_buttons()
    assert not refinement.btn1.disabled
    assert not refinement.btn2.disabled
    assert not refinement.alert.visible

@pytest.mark.asyncio
async def test_button_clicked_sets_and_resets_direction(widget):
    refinement = get_widget_instance(widget)

    # Replace the reco_explorer_app_instance with a mock that tracks calls
    mock_app = MockApp()
    mock_app.trigger_item_selection = AsyncMock()
    refinement.reco_explorer_app_instance = mock_app

    # Simulate a button click event with a name
    event = type('Event', (object,), {'obj': type('Obj', (object,), {'name': 'Mehr Diversität'})})()

    # Ensure direction is initially empty
    assert refinement.radio_box_group.params["direction"] == ""

    await refinement.button_clicked(event)

    # Check that the direction was set and then reset
    assert mock_app.trigger_item_selection.call_count == 1
    mock_app.trigger_item_selection.assert_called_once_with(event)
    assert refinement.radio_box_group.params["direction"] == ""