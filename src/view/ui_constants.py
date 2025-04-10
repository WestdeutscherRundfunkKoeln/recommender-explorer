#
# UI Constants
#
UI_CONFIG_KEY = "ui_config"
UI_CONFIG_TITLE_KEY = "title"
UI_CONFIG_LOGO_KEY = "logo"
UI_CONFIG_HEADER_BACKGROUND_COLOR_KEY = "header_background"
UI_CONFIG_PAGE_SIZE_KEY = "page_size"
UI_CONFIG_CUSTOM_CSS_KEY = "custom_css"
UI_CONFIG_PAGE_SIZE_KEY = "page_size"
FALLBACK_UI_PAGE_SIZE_VALUE = 4

# Text Input
TEXT_INPUT_PLACEHOLDER_KEY = "placeholder"
TEXT_INPUT_LABEL_KEY = "label"
TEXT_INPUT_VALIDATOR_KEY = "validator_function"
TEXT_INPUT_ACCESSOR_KEY = "accessor_function"
TEXT_INPUT_HAS_PAGING_KEY = ""
TEXT_INPUT_URL_PARAMETER_KEY = "url_parameter"
TEXT_INPUT_COMPONENT_GROUP_KEY = "component_group"
TEXT_INPUT_TOOLTIP_KEY = "tooltip"

# Multi Select
MULTI_SELECT_LABEL_KEY = "label"
MULTI_SELECT_DISPLAY_NAME_KEY = "display_name"
MULTI_SELECT_ITEM_DEFAULTS_KEY = "get_item_defaults"
MULTI_SELECT_OPTION_VALUE_KEY = "value"
MULTI_SELECT_OPTIONS_DEFAULT_FUNCTION_KEY = "option_default"
MULTI_SELECT_REGISTER_AS_KEY = "register_as"
MULTI_SELECT_LINKED_FILTER_NAME_KEY = "linked_filter_name"
MULTI_SELECT_FILTER_CATEGORY = "filter_category"
MULTI_SELECT_DISPLAY_NAME_KEY = "name"
MULTI_SELECT_OPTIONS_KEY = "options"
MULTI_SELECT_DICTIONARY_OPTIONS_KEY = "dictionary_options"
MULTI_SELECT_OPTION_LABEL_KEY = "display_name"
MULTI_SELECT_DEFAULT_OPTION_KEY = "default"
MULTI_SELECT_ACTION_OPTION_KEY = "action_option"
MULTI_SELECT_ACTION_OPTION_VALUE_KEY = "option_value"
MULTI_SELECT_ACTION_TARGET_WIDGET_KEY = "target_widget"
MULTI_SELECT_TOOLTIP_KEY = "tooltip"
MULTI_SELECT_PAGING = "has_paging"

# Reset Button
RESET_BUTTON_LABEL = "Auswahl zurücksetzen"
RESET_IDENTIFIER_ITEM_CHOICE = "item_choice"
RESET_IDENTIFIER_MODEL_CHOICE = "model_choice"
RESET_IDENTIFIER_ITEM_FILTER = "item_filter"
RESET_IDENTIFIER_UPPER_ITEM_FILTER = "upper_item_filter"
RESET_IDENTIFIER_RECO_FILTER = "reco_filter"
RESET_IDENTIFIER_UPPER_RECO_FILTER = "upper_reco_filter"

# Accordion Cards
ACCORDION_CARD_TOGGLE_KEY = "toggle"
ACCORDION_CARD_ACTIVE_KEY = "active"

# Accordion
ACCORDION_CONTENT_KEY = "content"
ACCORDION_LABEL_KEY = "label"
ACCORDION_ACTIVE_KEY = "active"
ACCORDION_RESET_BUTTON_KEY = "accordion-reset-button"
ACCORDION_MAX_WIDTH = 312


# Radio Box
RADIO_BOX_OPTION_KEY = "options"
RADIO_BUTTON_GROUP_OPTION_KEY = "options"


# Date Time Picker
DATE_TIME_PICKER_NAME_KEY = "name"
DATE_TIME_PICKER_VALIDATOR_KEY = "validator"
DATE_TIME_PICKER_LABEL_KEY = "label"
DATE_TIME_PICKER_ACCESSOR_KEY = "accessor_function"
DATE_TIME_PICKER_HAS_PAGING_KEY = "hasPaging"

DATE_TIME_QUICK_SELECT_LABEL_KEY = "label"
DATE_TIME_QUICK_SELECT_START_PICKER_LABEL_KEY = "start_picker_label"
DATE_TIME_QUICK_SELECT_END_PICKER_LABEL_KEY = "end_picker_label"
DATE_TIME_QUICK_SELECT_START_DELTA_DAYS = "start_delta_days"
DATE_TIME_QUICK_SELECT_END_DELTA_DAYS = "end_delta_days"

# Text Area Input
TEXT_AREA_INPUT_LABEL_KEY = "label"
TEXT_AREA_INPUT_PLACEHOLDER_KEY = "placeholder"
TEXT_AREA_INPUT_ACCESSOR_KEY = "accessor_function"
TEXT_AREA_INPUT_VALIDATOR_KEY = "validator_function"
TEXT_AREA_INPUT_URL_PARAMETER_KEY = "url_parameter"

TEXT_AREA_ROWS_NUM = "rows"
TEXT_AREA_MAX_ROWS_NUM = "max_rows"
AUTO_GROW = "auto_grow"
VISIBLE = "visible"


# Accordion Reset Button
ACCORDION_RESET_LABEL_KEY = "label"
ACCORDION_RESET_BUTTON_STYLE_KEY = "button-style"
ACCORDION_RESET_MARGIN_KEY = "margin"

# Slider
SLIDER_TYPE_VALUE = "slider"
SLIDER_LABEL_KEY = "label"
SLIDER_NAME_KEY = "name"
SLIDER_UNIT_KEY = "unit"
SLIDER_START_KEY = "start"
SLIDER_DEFAULT_KEY = "default"
SLIDER_END_KEY = "end"
SLIDER_STEP_KEY = "step"
SLIDER_COMPONENT_GROUP_KEY = "component_group"
SLIDER_TOOLTIP_KEY = "tooltip"

SLIDER_CUSTOM_KEY = "custom"

# Block
BLOCKS_CONFIG_KEY = "blocks"

BLOCKS_CONFIG_LINKTO = "linkto"
UI_ACC = "ui_acc"

BLOCK_LABEL_LIST_KEY = "label"
BLOCK_WIDGETS_LIST_KEY = "widgets"
BLOCK_CONFIG_LABEL_KEY = "label"
BLOCK_CONFIG_WIDGETS_KEY = "components"

# Common Ui Widget Types
WIDGET_TYPE_KEY = "type"
TEXT_INPUT_TYPE_VALUE = "text_field"
MULTI_SELECT_TYPE_VALUE = "multi_select"
ACCORDION_TYPE_VALUE = "accordion"
DATE_TIME_PICKER_TYPE_VALUE = "date_time_picker"
DATE_TIME_QUICK_SELECT_TYPE_VALUE = "date_time_quick_select"
RADIO_BOX_TYPE_VALUE = "radio_box"
TEXT_AREA_INPUT_TYPE_VALUE = "text_area_input"
ACCORDION_RESET_BUTTON_TYPE_VALUE = "accordion-reset-button"
ACCORDION_WITH_CARDS_TYPE_VALUE = "accordion_with_cards"

#Refeinement widget
REFINEMENT_WIDGET_TYPE_VALUE = "refinement_widget"
REFINEMENT_WIDGET_TOOLTIP = "Sie können zwischen verschiedenen Arten der Empfehlungsgenerierung für einen bestimmten Artikel wechseln und die Dimension des jeweiligen Typs verstärken."
REFINEMENT_WIDGET_ACCORDION_LABEL = "Empfehlungs-Typ"

# Fallbacks (if no key and value was given in the config yaml)
FALLBACK_UI_CONFIG_TITLE_VALUE = "Recommender Explorer"
FALLBACK_UI_CONFIG_LOGO_VALUE = ""
FALLBACK_UI_CONFIG_BACKGROUND_COLOR_VALUE = "#194569"
FALLBACK_UI_PAGE_SIZE_VALUE = 4
FALLBACK_TEXT_INPUT_LABEL_VALUE = "Default Text Label"
FALLBACK_MULTI_SELECT_OPTION_LABEL_VALUE = "Default Option Headline"
FALLBACK_MULTI_SELECT_LABEL_VALUE = "Default Multi Select Headline"
FALLBACK_ACCORDION_LABEL_VALUE = "Default Accordion Headline"
FALLBACK_DATE_TIME_PICKER_NAME_VALUE = "Default Date Time Picker Label"
FALLBACK_BLOCK_LABEL_VALUE = "Default Block Headline"
FALLBACK_TEXT_AREA_INPUT_LABEL_VALUE = "Default Text Area Input"

UI_CONFIG_BLOCKS = f"{UI_CONFIG_KEY}.{BLOCKS_CONFIG_KEY}"

TOOLTIP_FALLBACK = "!! Hinterlegen Sie bitte einen beschreibenden Text zu diesem Parameter in der UI-Configuration.!!"
FILTER_WIDTH = 258


# Content Cards
INSERT_ID_BUTTON_LABEL = "Als Start Item übernehmen"

# UI Elements
UP_ARROW = "\u25b2"
DOWN_ARROW = "\u25bc"
RIGHT_ARROW = "\u25b6"
LEFT_ARROW = "\u25c0"
