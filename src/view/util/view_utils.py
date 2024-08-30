import logging
import panel as pn
from typing import List, Tuple
from view.widgets.radio_box_widget import RadioBoxWidget
from view.widgets.radio_box_widget import WidgetGroupWrapper

logger = logging.getLogger(__name__)


def get_first_widget_by_accessor_function(widget, target_accessor):
    """
    This method searches for a widget using the provided target accessor function. It first checks if the widget is a nested widget by calling
    the _process_nested_widgets function recursively. If a nested widget is found, it is returned. If no nested widget is found, it checks if
    the widget has a 'params' attribute and if the 'accessor' key is present in widget.params with a value matching the target_accessor.
    If a match is found, the widget is returned. If no widget is found matching the target_accessor, None is returned.

    :param widget: The widget from which to search for the target widget.
    :param target_accessor: The accessor function used to identify the target widget.
    :return: The target widget if found, otherwise None.
    """
    if (
        hasattr(widget, "params")
        and "accessor" in widget.params
        and widget.params["accessor"] == target_accessor
    ):
        return widget
    return _process_nested_widgets(widget, target_accessor)


def _process_nested_widgets(widget, target_accessor):
    """
    Process nested widgets to find a specific widget by its target accessor.

    :param widget: The parent widget to search for nested widgets.
    :param target_accessor: The target accessor of the widget to find.
    :return: The found widget with the target accessor, or None if not found.
    """
    if hasattr(widget, "objects"):
        for child in widget.objects:
            result = get_first_widget_by_accessor_function(child, target_accessor)
            if result is not None:
                return result


def get_custom_radio_box_widgets(widgets) -> List[RadioBoxWidget]:
    """
    Get all custom radio box widgets from the given widget.

    :param widgets: The widget to search for custom radio box widgets.
    :return: A list of custom radio box widgets found in the given widget.
    """
    radio_box_widgets = []
    if isinstance(widgets, RadioBoxWidget):
        radio_box_widgets.append(widgets)
    else:
        if hasattr(widgets, "objects"):
            radio_box_widgets += [
                radio_child
                for obj in widgets.objects
                for radio_child in get_custom_radio_box_widgets(obj)
            ]
    return radio_box_widgets


def extract_widgets_from_radio_box_widget(
    radio_box_widget: RadioBoxWidget,
) -> Tuple[pn.widgets.RadioBoxGroup, List[WidgetGroupWrapper]]:
    """
    Get panel radio box group and widgets groups from the given custom RadioBoxGroup.

    :param radio_box_widget: The radio box widget from which to extract widgets
    :return: A tuple containing the radio box group widget and a list of widget group wrappers
    """
    radio_box_group = None
    widget_group_wrappers = []
    for widget in radio_box_widget:
        if isinstance(widget, pn.widgets.RadioBoxGroup) and radio_box_group is None:
            radio_box_group = widget
        elif isinstance(widget, WidgetGroupWrapper):
            widget_group_wrappers.append(widget)
    return radio_box_group, widget_group_wrappers
