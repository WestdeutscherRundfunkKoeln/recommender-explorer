##############################################
### Constants used throughout RecoExplorer ###
##############################################

#
# Item constants
#

ITEM_POSITION_START = 'start'
ITEM_POSITION_RECO = 'reco'

ITEM_TYPE_USER = 'user'
ITEM_TYPE_CONTENT = 'content'

ITEM_PROVENANCE_U2C = 'u2c_models'
ITEM_PROVENANCE_C2C = 'c2c_models'

#
# Model constants
#

MODEL_TYPE_C2C = ITEM_PROVENANCE_C2C
MODEL_TYPE_U2C = ITEM_PROVENANCE_U2C

MODEL_CONFIG_C2C = 'c2c_config'
MODEL_CONFIG_U2C = 'u2c_config'

#
# Display constants
#

DISPLAY_MODE_MULTI = 'multi'
DISPLAY_MODE_SINGLE = 'single'

#
# System constants
#
CLIENT_IDENTIFIER = 'client'

#
# UI Constants
#
UI_CONFIG_KEY = 'ui_config'
UI_CONFIG_TITLE_KEY = 'title'
UI_CONFIG_LOGO_KEY = 'logo'
UI_CONFIG_HEADER_BACKGROUND_COLOR_KEY = 'header_background'
UI_CONFIG_CUSTOM_CSS_KEY = 'custom_css'

# Text Input
TEXT_INPUT_PLACEHOLDER_KEY = 'placeholder'
TEXT_INPUT_LABEL_KEY = 'label'
TEXT_INPUT_VALIDATOR_KEY = 'validator_function'
TEXT_INPUT_ACCESSOR_KEY = 'accessor_function'
TEXT_INPUT_HAS_PAGING_KEY = ''
TEXT_INPUT_URL_PARAMETER_KEY = 'url_parameter'

# Multi Select Options
MULTI_SELECT_OPTIONS_KEY = 'options'
MULTI_SELECT_OPTION_LABEL_KEY = 'display_name'
MULTI_SELECT_DEFAULT_OPTION_KEY = 'default'

# Multi Select
MULTI_SELECT_LABEL_KEY = 'label'

# Accordion
ACCORDION_CONTENT_KEY = 'content'
ACCORDION_LABEL_KEY = 'label'
ACCORDION_ACTIVE_KEY = 'active'
ACCORDION_TOGGLE_KEY = 'toggle'

# Block
BLOCKS_CONFIG_KEY = 'blocks'
BLOCK_LABEL_LIST_KEY = 'label'
BLOCK_WIDGETS_LIST_KEY = 'widgets'
BLOCK_CONFIG_LABEL_KEY = 'label'
BLOCK_CONFIG_WIDGETS_KEY = 'components'

# Common Ui Widget Types
WIDGET_TYPE_KEY = 'type'
TEXT_INPUT_TYPE_VALUE = 'text_field'
MULTI_SELECT_TYPE_VALUE = 'multi_select'
ACCORDION_TYPE_VALUE = 'accordion'


# Fallbacks (if no key and value was given in the config yaml)
FALLBACK_UI_CONFIG_TITLE_VALUE = 'Recommender Explorer'
FALLBACK_UI_CONFIG_LOGO_VALUE = ''
FALLBACK_UI_CONFIG_BACKGROUND_COLOR_VALUE = '#194569'
FALLBACK_TEXT_INPUT_LABEL_VALUE = 'Default Text Label'
FALLBACK_MULTI_SELECT_OPTION_LABEL_VALUE = 'Default Option Headline'
FALLBACK_MULTI_SELECT_LABEL_VALUE = 'Default Multi Select Headline'
FALLBACK_ACCORDION_LABEL_VALUE = 'Default Accordion Headline'
FALLBACK_BLOCK_LABEL_VALUE = 'Default Block Headline'



