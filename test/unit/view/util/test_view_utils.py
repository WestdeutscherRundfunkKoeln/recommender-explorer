import panel as pn

from src.view.util.view_utils import (
    collect_leaf_widgets,
    get_first_widget_by_accessor_function,
    find_widget_by_name_recursive,
    find_widget_by_type_and_label,
)


def test_get_first_widget_by_accessor_function():
    text_input_1 = pn.widgets.TextInput(name="1")
    text_input_1.params = {"accessor": "test_accessor"}
    text_input_2 = pn.widgets.TextInput(name="2")
    text_input_2.params = {"accessor": "test_accessor"}
    text_input_3 = pn.widgets.TextInput(name="3")
    text_input_3.params = {"accessor": "other_test_accessor"}
    markdown = pn.pane.Markdown()
    card = pn.Card(objects=[markdown, text_input_3])
    row = pn.Row(objects=[text_input_2, card])
    col = pn.Column(objects=[text_input_1, row])

    assert get_first_widget_by_accessor_function(col, "test_accessor") == text_input_2
    assert (
        get_first_widget_by_accessor_function(col, "other_test_accessor")
        == text_input_3
    )


def test_find_widget_by_name_recursive():
    text_input_1 = pn.widgets.TextInput(name="1")
    text_input_2 = pn.widgets.TextInput(name="1")
    text_input_3 = pn.widgets.TextInput(name="2")
    markdown = pn.pane.Markdown()
    card = pn.Card(objects=[markdown, text_input_3])
    row = pn.Row(objects=[text_input_2, card])
    col = pn.Column(objects=[text_input_1, row])

    assert find_widget_by_name_recursive(col, "1") == text_input_2
    assert find_widget_by_name_recursive(col, "2") == text_input_3
    assert find_widget_by_name_recursive(col, "2", True) == card


def test_collect_leaf_widgets():
    text_input_1 = pn.widgets.TextInput(name="1")
    text_input_1.is_leaf_widget = True
    text_input_1.reset_identifier = "test1"
    text_input_2 = pn.widgets.TextInput(name="2")
    text_input_2.is_leaf_widget = True
    text_input_2.reset_identifier = "test2"
    text_input_3 = pn.widgets.TextInput(name="3")
    text_input_3.is_leaf_widget = True
    text_input_3.reset_identifier = "test3"
    icon = pn.widgets.indicators.TooltipIcon()
    special_row = pn.Row(objects=[text_input_3, icon])
    row = pn.Row(objects=[text_input_2, special_row])
    col = pn.Column(objects=[text_input_1, row])

    assert collect_leaf_widgets(col, (pn.layout.Column, pn.layout.Row)) == {
        text_input_1,
        text_input_2,
        text_input_3,
    }


def test_find_widget_by_type_and_label():
    date_picker_1 = pn.widgets.DatePicker(name="1")
    date_picker_1.params = {"label": "test1"}
    date_picker_2 = pn.widgets.DatePicker(name="2")
    date_picker_2.params = {"label": "test2"}
    text_input = pn.widgets.TextInput(name="3")
    text_input.params = {"label": "test3"}
    markdown = pn.pane.Markdown()
    card = pn.Card(objects=[markdown, text_input])
    row = pn.Row(objects=[date_picker_2, card])
    col = pn.Column(objects=[date_picker_1, row])

    assert (
        find_widget_by_type_and_label(col, pn.widgets.DatePicker, "test1")
        == date_picker_1
    )
    assert (
        find_widget_by_type_and_label(col, pn.widgets.DatePicker, "test2")
        == date_picker_2
    )
    assert find_widget_by_type_and_label(col, pn.widgets.DatePicker, "test3") is None
