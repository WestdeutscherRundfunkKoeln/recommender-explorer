from datetime import datetime
from dateutil.relativedelta import relativedelta
from src.dto.content_item import ContentItemDto
import constants

def mock_start_filter_component(filter_values: dict) -> object:
    item_filter = lambda : None
    item_filter.params = {}
    item_filter.params['label'] = filter_values['label']
    item_filter.value = filter_values['selected_value']
    item_filter.visible = True
    return item_filter

def mock_reco_filter_component(filter_values: dict) -> object:
    item_filter = lambda : None
    item_filter.params = {}
    item_filter.params['label'] = filter_values['label']
    item_filter.value = filter_values['selected_value']
    item_filter.visible = True
    return item_filter

def mock_date_component(date_values: dict, position: str) -> object:
    date_choice = lambda: None
    date_choice.params = {}
    date_choice.params['label'] = position + date_values['label']
    date_choice.params['validator'] = date_values['validator']
    date_choice.params['accessor'] = date_values['accessor']
    date_choice.params['has_paging'] = date_values['has_paging']
    date_choice.visible = True
    date_choice.name = position.capitalize() + 'datum'
    if position == 'start':
        date_choice.value = datetime.now() + relativedelta(months=-3)
    else:
        date_choice.value = datetime.now()
    return date_choice

def mock_user_component(values: list) -> object:
    user_choice = lambda: None
    user_choice.params = {}
    user_choice.params['active'] = values[0]
    user_choice.params['label'] = values[1]
    user_choice.params['validator'] = values[2]
    user_choice.params['has_paging'] = True
    user_choice.value = values[3]
    user_choice.name = 'test_category'
    return user_choice

def mock_model_component(values: list) -> object:
    model = lambda: None
    model.params = {}
    model.params['label'] = values[1]
    model.value = [values[0]]
    return model

def mock_start_and_reco_items_with_duplicates() -> object:
    start_item = ContentItemDto(_position = constants.ITEM_POSITION_START, _item_type = constants.ITEM_TYPE_CONTENT, _provenance = constants.ITEM_PROVENANCE_C2C, description='Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam', crid='crid://video1')
    reco_items = [ContentItemDto(_position = constants.ITEM_POSITION_RECO, _item_type = constants.ITEM_TYPE_CONTENT, _provenance = constants.ITEM_PROVENANCE_C2C, description='nonumy eirmod tempor invidunt ut labore', crid='crid://video2'),
                  ContentItemDto(_position = constants.ITEM_POSITION_RECO, _item_type = constants.ITEM_TYPE_CONTENT, _provenance = constants.ITEM_PROVENANCE_C2C, description='et dolore magna aliquyam erat, sed diam voluptua.', crid='crid://video1'),
                  ContentItemDto(_position = constants.ITEM_POSITION_RECO, _item_type = constants.ITEM_TYPE_CONTENT, _provenance = constants.ITEM_PROVENANCE_C2C, description='At vero eos et accusam et justo duo dolores et ea rebum.', crid='crid://video3'),
                  ContentItemDto(_position = constants.ITEM_POSITION_RECO, _item_type = constants.ITEM_TYPE_CONTENT, _provenance = constants.ITEM_PROVENANCE_C2C, description='Stet clita kasd gubergren', crid='crid://video4'),
                  ContentItemDto(_position = constants.ITEM_POSITION_RECO, _item_type = constants.ITEM_TYPE_CONTENT, _provenance = constants.ITEM_PROVENANCE_C2C, description='et dolore magna aliquyam erat, sed diam voluptua.', crid='crid://video5'),
                  ContentItemDto(_position = constants.ITEM_POSITION_RECO, _item_type = constants.ITEM_TYPE_CONTENT, _provenance = constants.ITEM_PROVENANCE_C2C, description='no sea takimata sanctus est Lorem ipsum dolor sit amet.', crid='crid://video2'),
                  ContentItemDto(_position = constants.ITEM_POSITION_RECO, _item_type = constants.ITEM_TYPE_CONTENT, _provenance = constants.ITEM_PROVENANCE_C2C, description='Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam', crid='crid://video6')]
    return start_item, reco_items