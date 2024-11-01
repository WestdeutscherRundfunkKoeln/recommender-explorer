from unittest.mock import MagicMock

import pytest

from view.widgets.radio_box_widget import RadioBoxWidget


@pytest.fixture
def radio_box_widget_fixture(create_text_field_widget, create_date_time_picker_widget, create_text_area_input_widget):
    def _radio_box_widget(config: dict) -> RadioBoxWidget:
        widget_dispatcher = {
            "text_field": create_text_field_widget,
            'date_time_picker': create_date_time_picker_widget,
            'text_area_input': create_text_area_input_widget,
        }
        reco_explorer_app_instance = MagicMock()
        reco_explorer_app_instance.build_common_ui_widget_dispatcher.side_effect = lambda w_type, w_cfg: widget_dispatcher[w_type](w_cfg)
        controller_instance = MagicMock()
        widget = RadioBoxWidget(reco_explorer_app_instance, controller_instance)
        return widget.create(config)

    return _radio_box_widget
