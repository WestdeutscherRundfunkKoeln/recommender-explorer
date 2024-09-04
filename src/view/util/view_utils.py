import logging
from collections import deque
from typing import Callable, TypeVar, cast, List, Tuple
from view.widgets.radio_box_widget import RadioBoxWidget
from view.widgets.radio_box_widget import WidgetGroupWrapper

import panel as pn

logger = logging.getLogger(__name__)

WidgetWithCildren = (pn.layout.ListPanel, pn.layout.base.NamedListPanel)
T = TypeVar("T")


def get_first_widget_by_accessor_function(
    widget: pn.viewable.Viewable, target_accessor: list[str]
) -> pn.viewable.Viewable | None:
    """
    This method searches for a widget using the provided target accessor function. It first checks if the widget is a nested widget by calling
    the _process_nested_widgets function recursively. If a nested widget is found, it is returned. If no nested widget is found, it checks if
    the widget has a 'params' attribute and if the 'accessor' key is present in widget.params with a value matching the target_accessor.
    If a match is found, the widget is returned. If no widget is found matching the target_accessor, None is returned.

    :param widget: The widget from which to search for the target widget.
    :param target_accessor: The accessor function used to identify the target widget.
    :return: The target widget if found, otherwise None.
    """

    def _widget_with_accessor(w):
        return (
            hasattr(w, "params")
            and "accessor" in w.params
            and w.params["accessor"] in target_accessor
        )

    return find_widget(widget, _widget_with_accessor)


def collect_leaf_widgets(
    widget: pn.viewable.Viewable,
    layout_widget_types: tuple[
        type[pn.layout.ListPanel] | type[pn.layout.base.NamedListPanel], ...
    ],
) -> set[pn.viewable.Viewable]:
    """
    This method collects leaf widgets from a given widget.

    :param widget: The widget from which to collect leaf widgets.
    :return: A list of leaf widgets.

    The leaf widgets are collected recursively by traversing through the widget hierarchy.
    Leaf widgets are considered to be widgets with the attribute `is_leaf_widget` set to
    `True`. If the widget is an instance of one of the layout widget types specified in
    `layout_widget_types`, the method recursively collects leaf widgets from its children.
    """

    return collect_widgets(
        widget, lambda w: hasattr(w, "is_leaf_widget") and getattr(w, "is_leaf_widget")
    )


def find_widget_by_name(
    widget: pn.reactive.Reactive, target_name: str, return_parent: bool = False
) -> pn.viewable.Viewable | None:
    """
    Gets a widget from a widget group (for example panels widgets box) and search it by given name (label).
    Calls itself for nested widgets (recursive).

    If return_parent is set to True, the function will return containing widget of the target widget
    instead of the target widget itself.

    :param widget: Widget that is the source for the search.
    :param target_name: Name of the target widget.
    :param return_parent: If set to True, return the container of the widget found.
    :return: The widget or container of widget if found, or None if no widget found.
    """

    def _find_parent(w):
        if isinstance(w, (pn.layout.ListPanel, pn.layout.base.NamedListPanel)):
            for child in w:
                if hasattr(child, "name") and child.name == target_name:
                    return True
        return False

    if return_parent:
        return find_widget(widget, _find_parent)

    return find_widget(widget, lambda w: hasattr(w, "name") and w.name == target_name)


def find_widget_by_type(
        widget: pn.viewable.Viewable, widget_type: type[T]
) -> T | None:
    """
    Finds all widget of a certain type in a given widget collection.

    param widget: The widget to search for the target widget.
    param widget_type: The type of the target widget.
    return: The target widget if found, otherwise None.
    """

    def _predicate(w):
        return (
            isinstance(w, widget_type)
        )

    return cast(T | None, find_widget(widget, _predicate))


def find_widget_by_type_and_label(
    widget: pn.viewable.Viewable, widget_type: type[T], label: str
) -> T | None:
    """
    Finds all widget of a certain type with a certain label in a given widget collection.

    param widget: The widget to search for the target widget.
    param widget_type: The type of the target widget.
    param label: The label of the target widget.
    return: The target widget if found, otherwise None.
    """

    def _predicate(w):
        return (
            isinstance(w, widget_type)
            and hasattr(w, "params")
            and getattr(w, "params").get("label") == label
        )

    return cast(T | None, find_widget(widget, _predicate))


def find_widget(
    start_widget: pn.viewable.Viewable,
    predicate: Callable[[pn.viewable.Viewable], bool],
) -> pn.viewable.Viewable | None:
    """
    performs a breadth-first search on the widget tree starting at start_widget and returns the first widget for which the predicate is True.

    param start_widget: The widget to start the search from.
    param predicate: The predicate to test each widget against.
    return: The first widget for which the predicate is True, or None if no such widget is found.
    """
    queue = deque([start_widget])
    while queue:
        current = queue.popleft()
        if predicate(current):
            return current
        if isinstance(current, WidgetWithCildren):
            queue.extend([widget for widget in current])


def collect_widgets(
    start_widget: pn.viewable.Viewable,
    predicate: Callable[[pn.viewable.Viewable], bool],
) -> set[pn.viewable.Viewable]:
    """
    performs a depth-first search on the widget tree starting at start_widget and returns all widgets for which the predicate is True.

    param start_widget: The widget to start the search from.
    param predicate: The predicate to test each widget against.
    return: All widgets for which the predicate is True.
    """
    widgets = set()
    stack = [start_widget]
    while stack:
        current = stack.pop()
        if predicate(current):
            widgets.add(current)
        if isinstance(current, WidgetWithCildren):
            stack.extend([widget for widget in current])
    return widgets
