import pytest
import panel as pn
from view.widgets.refinement_widget import RefinementWidget, DIVERSITY, RECENCY

class MockApp:
    async def trigger_item_selection(self, event): pass
    async def trigger_reco_filter_choice(self, *args): pass

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
    assert radio.value == "Ähnlichkeit"
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

    await refinement.update_buttons(type('Event', (object,), {'new': "Unknown"}))
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
