import logging
from typing import Callable, Any

import view.ui_constants as c
from dto.item import ItemDto
from view.widgets.radio_box_widget import RadioBoxWidget
from view.widgets.radio_box_widget import WidgetGroupWrapper
from view.util.view_utils import find_widget_by_type
from view.util.view_utils import get_first_widget_by_accessor_function

import panel as pn

logger = logging.getLogger(__name__)


def create_click_handler(
        external_id: str, widgets: pn.viewable.Viewable
) -> Callable[[Any], None]:
    """
    Create a click handler function that sets the value of a target widget
    to the external_id. Uses view utils function to get widget by accessor name.

    :param widgets: a list of widgets to search in
    :param external_id: The external ID.
    :return: The click handler function.
    """

    def click_handler(event):
        radio_box_widget = find_widget_by_type(widgets, RadioBoxWidget)

        if radio_box_widget:
            radio_box_group, widget_groups = _extract_widgets_from_radio_box_widget(radio_box_widget)
            _get_target_widget_from_radio_box_set_value_and_select_option(radio_box_group, widget_groups, external_id)
        else:
            _get_target_widget_set_value(widgets, external_id)

    return click_handler


def _extract_widgets_from_radio_box_widget(
        radio_box_widget: RadioBoxWidget,
) -> tuple[pn.widgets.RadioBoxGroup, list[WidgetGroupWrapper]]:
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


def _get_target_widget_from_radio_box_set_value_and_select_option(
        radio_box_group: pn.widgets.RadioBoxGroup,
        widget_groups: list[WidgetGroupWrapper],
        external_id: str
):
    """
    Sets the value of the target widget identified by the given external_id and selects the correct
    option in the radio box widget.

    :param radio_box_group: the radio box group that contains the options for selecting a widget
    :param widget_groups: a list of widget groups that contains the target widget
    :param external_id: the value to set for the target widget
    :return: the target widget if found, None otherwise
    """
    for widget_group in widget_groups:
        target_widget = get_first_widget_by_accessor_function(widget_group, ["get_item_by_crid"])

        if target_widget and widget_group.option_of_widget_group in radio_box_group.options:
            radio_box_group.value = widget_group.option_of_widget_group
            target_widget.value = external_id
            break


def _get_target_widget_set_value(
        widgets: pn.viewable.Viewable,
        external_id: str
):
    """
    Sets the value of the target widget identified by the given external_id.

    :param widgets: a list of widgets to search in
    :param external_id: the external_id used to identify the target widget
    :return: None
    """
    target_widget = get_first_widget_by_accessor_function(widgets, ["get_item_by_crid", "get_item_by_external_id"])
    if target_widget:
        target_widget.value = external_id


def insert_id_button(
        click_handler: Callable
) -> pn.widgets.Button:
    """
    Creates and returns a Button widget and assigns the
    specified click_handler function to its on_click event.

    :param click_handler: The function to be called when the button is clicked.
    :return: A Button widget with the assigned click_handler function for the on_click event.
    """
    insert_id_button_widget = pn.widgets.Button(name=c.INSERT_ID_BUTTON_LABEL)
    insert_id_button_widget.on_click(click_handler)
    return insert_id_button_widget


def append_custom_css_for_insert_id_button(
        config: dict[str, Any],
        model_config: str,
        content_dto: ItemDto,
        model: dict[str, Any]
):
    """
    Appends custom CSS for the "insert id button" on the recommended item card. Colors depends on
    the start item and reco items card color from the config.

    :param config:
    :param model_config: The configuration for the model.
    :param content_dto: The data transfer object for the content.
    :param model: The model to append the custom CSS for.

    :return: None
    """
    css = f"""
            .bk.bk-btn.bk-btn-default {{
                background-color: {config[model_config][content_dto.provenance][model]["start_color"]} !important;
                font-weight: bolder;
            }}
            .bk.bk-btn.bk-btn-default:hover {{
                border-color: {config[model_config][content_dto.provenance][model]["reco_color"]} !important;
            }}
            """
    pn.extension(raw_css=[css])
