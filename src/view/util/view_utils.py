import logging

logger = logging.getLogger(__name__)


def get_widget_by_accessor_function(widget, target_accessor):
    """
    This method searches for a widget using the provided target accessor function. It first checks if the widget is a nested widget by calling
    the _process_nested_widgets function recursively. If a nested widget is found, it is returned. If no nested widget is found, it checks if
    the widget has a 'params' attribute and if the 'accessor' key is present in widget.params with a value matching the target_accessor.
    If a match is found, the widget is returned. If no widget is found matching the target_accessor, None is returned.

    :param widget: The widget from which to search for the target widget.
    :param target_accessor: The accessor function used to identify the target widget.
    :return: The target widget if found, otherwise None.
    """
    nested_widget_result = _process_nested_widgets(widget, target_accessor)
    if nested_widget_result is not None:
        return nested_widget_result
    if hasattr(widget, 'params') and "accessor" in widget.params and widget.params["accessor"] == target_accessor:
        return widget


def _process_nested_widgets(widget, target_accessor):
    """
    Process nested widgets to find a specific widget by its target accessor.

    :param widget: The parent widget to search for nested widgets.
    :param target_accessor: The target accessor of the widget to find.
    :return: The found widget with the target accessor, or None if not found.
    """
    if 'objects' in dir(widget):
        for child in widget.objects:
            result = get_widget_by_accessor_function(child, target_accessor)
            if result is not None:
                return result
