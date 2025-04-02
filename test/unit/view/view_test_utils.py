import pytest
import panel as pn


def _validate_widget_type(widget: pn.viewable.Viewable, assert_type: type):
    assert isinstance(widget, assert_type)


def _validate_widget_properties(
        text_input_widget: pn.viewable.Viewable,
        expected_properties: dict,
):
    for property_name, expected_value in expected_properties.items():
        actual_value = getattr(text_input_widget, property_name)
        assert actual_value == expected_value, \
            f"{property_name} does not match expected value. Got {actual_value}, expected {expected_value}"


def _get_count_of_a_specific_widget(panel_widget, widget_type):
    widget_count = 0

    if isinstance(panel_widget, widget_type):
        widget_count += 1
    else:
        if isinstance(panel_widget, (pn.Column, pn.Row, pn.WidgetBox)):
            for child in panel_widget:
                widget_count += _get_count_of_a_specific_widget(child, widget_type)

    return widget_count
