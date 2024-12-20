import asyncio
import logging
import traceback
import functools
from typing import Any

import constants
import panel as pn
from controller.reco_controller import RecommendationController
from exceptions.date_validation_error import DateValidationError
from exceptions.empty_search_error import EmptySearchError
from exceptions.model_validation_error import ModelValidationError
from util.dto_utils import dto_from_classname
from util.file_utils import (
    get_client_options,
)
from view import ui_constants
from view.widgets.accordion_widget import AccordionWidget
from view.widgets.date_time_picker_widget import DateTimePickerWidget
from view.widgets.date_time_quick_select_widget import DateTimeQuickSelectWidget
from view.widgets.multi_select_widget import MultiSelectionWidget
from view.widgets.radio_box_widget import RadioBoxWidget
from view.widgets.reset_button import ResetButtonWidget
from view.widgets.slider_widget import SliderWidget
from view.widgets.text_area_input_widget import TextAreaInputWidget
from view.widgets.text_field_widget import TextFieldWidget
from view.widgets.accordion_widget import AccordionWidgetWithCards

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
#
# Main App
#
class RecoExplorerApp:
    def __init__(
        self, config_full_paths: dict[str, str], config: dict[str, str], client: str
    ) -> None:
        # basic setup
        self.config = config
        self.client = client
        self.config_full_paths = config_full_paths
        self.config_full_path = config_full_paths[client]
        self.controller = RecommendationController(self.config)

        self.widgets = {
            ui_constants.MULTI_SELECT_TYPE_VALUE: MultiSelectionWidget(
                self, self.controller
            ),
            ui_constants.DATE_TIME_PICKER_TYPE_VALUE: DateTimePickerWidget(
                self, self.controller
            ),
            ui_constants.TEXT_INPUT_TYPE_VALUE: TextFieldWidget(
                self, self.controller
            ),
            ui_constants.RADIO_BOX_TYPE_VALUE: RadioBoxWidget(
                self, self.controller
            ),
            ui_constants.ACCORDION_TYPE_VALUE: AccordionWidget(
                self, self.controller
            ),
            ui_constants.SLIDER_TYPE_VALUE: SliderWidget(
                self, self.controller
            ),
            ui_constants.TEXT_AREA_INPUT_TYPE_VALUE: TextAreaInputWidget(
                self, self.controller
            ),
            ui_constants.ACCORDION_WITH_CARDS_TYPE_VALUE: AccordionWidgetWithCards(
                self, self.controller
            ),
            ui_constants.DATE_TIME_QUICK_SELECT_TYPE_VALUE: DateTimeQuickSelectWidget(
                self, self.controller
            ),
        }

        pn.extension(sizing_mode="stretch_width")
        pn.extension("floatpanel")

        # display mode
        self.display_mode = constants.DISPLAY_MODE_SINGLE

        # display mode
        self.model_type = constants.MODEL_CONFIG_C2C

        # start items
        self.start_items = []

        # reco items
        self.recos = []

        # all the c2c and u2c models available in this app
        self.c2c_models = []
        self.c2c_model_default = []
        self.u2c_models = []

        #
        self.nav_controls = pn.WidgetBox()
        self.navigational_components = {}
        self.config_based_nav_controls = pn.WidgetBox()
        self.client_choice_visibility = len(self.config_full_paths) > 1

        #
        self.define_item_pagination()
        if ui_constants.UI_CONFIG_KEY not in self.config:
            self.define_start_item_selections()
            self.define_start_item_filtering()
            self.define_reco_filtering_selection()
            self.define_reco_filtering_selection_u2c()
            self.define_reco_sorting()
            self.define_reco_duplicate_filtering()
            self.define_reco_incomplete_filtering()
            self.define_model_selections()
            self.define_user_selections()
            self.define_reco_duration_filtering()
            self.define_score_threshold()

        self.template = pn.template.BootstrapTemplate()
        self.main_content = pn.Column()
        self.page_size = self.define_page_size()

        # init some of the component values
        self.set_c2c_model_definitions()
        self.set_u2c_model_definitions()

        self.url_parameter_text_field_mapping = {}

    def set_c2c_model_definitions(self):
        models = self.config[constants.MODEL_CONFIG_C2C][constants.MODEL_TYPE_C2C]
        for model in models.keys():
            self.c2c_models.append(model)
            if models[model]["default"]:
                self.c2c_model_default.append(model)

    def set_u2c_model_definitions(self):
        if constants.MODEL_CONFIG_U2C in self.config:
            models = self.config[constants.MODEL_CONFIG_U2C][constants.MODEL_TYPE_U2C]
            for model in models.keys():
                self.u2c_models.append(model)
        else:
            logger.error("u2c feature disabled")

    # pn component definitions
    def define_item_pagination(self):
        self.pagination = pn.Row()
        self.floating_elements = pn.Row(height=0, width=0)

    def define_start_item_filtering(self):
        # genre selector
        self.genreRadio = pn.widgets.RadioBoxGroup(
            name="erzählweiseGenreRadio",
            options={"Erzählweise": "choose_upper_genre", "Genre": "choose_genre"},
            visible=True,
        )

        self.genreRadio.params = {
            "label": "erzählweiseGenreRadio",
            "visible_action": ("choose_upper_genre", "erzaehlweise"),
            "visible_action_2": ("choose_genre", "genres"),
            "reset_to": None,
        }

        self.genreRadio_watcher = self.genreRadio.param.watch(
            self.toggle_visibility, "value", onlychanged=True
        )
        self.controller.register(
            "upper_item_filter",
            self.genreRadio,
            self.genreRadio_watcher,
            self.toggle_visibility,
        )

        self.erzaehlweise = pn.widgets.MultiSelect(
            options={
                "Genres Doku": "categories_documentation",
                "Genres Fiktion": "categories_fiction",
                "Genres Show": "categories_show",
                "Genres Information": "categories_information",
                "Genres Live": "categories_live",
            },
            visible=True,
            size=5,
        )

        self.erzaehlweise.params = {"label": "erzaehlweiseCategory", "reset_to": []}

        self.erzaehlweise.param.watch(
            self.toggle_genre_selection_by_upper_genre, "value", onlychanged=True
        )
        self.controller.register("upper_item_filter", self.erzaehlweise)

        self.genres = pn.widgets.MultiSelect(options=[], visible=False, size=4)

        self.genres.params = {"label": "genreCategory", "reset_to": []}

        self.genres.options = self.controller.get_item_defaults("genreCategory")
        self.genres.param.watch(self.toggle_start_components, "visible")
        self.genres.param.watch(self.trigger_filter_choice, "value", onlychanged=True)
        self.controller.register("item_filter", self.genres)

        self.genre_start_col = pn.Column(
            self.genreRadio, self.erzaehlweise, self.genres
        )

        # subgenre selector
        self.subgenreRadio = pn.widgets.RadioBoxGroup(
            name="inhaltSubgenreRadio",
            options={"Inhalt": "choose_upper_subgenre", "Subgenre": "choose_subgenre"},
            visible=True,
        )

        self.subgenreRadio.params = {
            "label": "inhaltSubgenreRadio",
            "visible_action": ("choose_upper_subgenre", "inhalt"),
            "visible_action_2": ("choose_subgenre", "subgenres"),
            "reset_to": None,
        }

        self.subgenreRadio_watcher = self.subgenreRadio.param.watch(
            self.toggle_visibility, "value", onlychanged=True
        )
        self.controller.register(
            "upper_item_filter",
            self.subgenreRadio,
            self.subgenreRadio_watcher,
            self.toggle_visibility,
        )

        self.inhalt = pn.widgets.MultiSelect(
            options={
                "Subgenres Doku": "categories_documentation",
                "Subgenres Fiktion": "categories_fiction",
                "Subgenres Show": "categories_show",
                "Subgenres Information": "categories_information",
                "Subgenres Live": "categories_live",
            },
            visible=True,
            size=5,
        )

        self.inhalt.params = {"label": "inhaltCategory", "reset_to": []}

        self.inhalt.param.watch(
            self.toggle_genre_selection_by_upper_genre, "value", onlychanged=True
        )
        self.controller.register("upper_item_filter", self.inhalt)

        self.subgenres = pn.widgets.MultiSelect(options=[], visible=False, size=4)

        self.subgenres.params = {"label": "subgenreCategories", "reset_to": []}

        self.subgenres.options = self.controller.get_item_defaults("subgenreCategories")
        self.subgenres.param.watch(self.toggle_start_components, "visible")
        self.subgenres.param.watch(
            self.trigger_filter_choice, "value", onlychanged=True
        )
        self.controller.register("item_filter", self.subgenres)

        self.subgenre_start_col = pn.Column(
            self.subgenreRadio, self.inhalt, self.subgenres
        )

        # theme selector
        self.themes = pn.widgets.MultiSelect(
            name="Themen", options=[], visible=True, size=4
        )

        self.themes.params = {"label": "thematicCategories", "reset_to": []}

        self.themes.options = self.controller.get_item_defaults("thematicCategories")
        self.themes.param.watch(self.toggle_start_components, "visible")
        self.themes.param.watch(self.trigger_filter_choice, "value", onlychanged=True)
        self.controller.register("item_filter", self.themes)

        # show selector
        self.shows = pn.widgets.MultiSelect(
            name="Sendereihen", options=[], visible=True, size=4
        )

        self.shows.params = {"label": "showTitel", "reset_to": []}

        self.shows.options = self.controller.get_item_defaults("showTitle")
        self.shows.param.watch(self.toggle_start_components, "visible")
        self.shows.param.watch(self.trigger_filter_choice, "value", onlychanged=True)
        self.controller.register("item_filter", self.shows)

        # reset button
        self.item_resetter = pn.widgets.Button(
            name="Auswahl zurücksetzen", button_type="primary", margin=10
        )

        self.item_resetter.params = {
            "label": "item_resetter",
            "resets": ["item_choice", "upper_item_filter", "item_filter"],
        }

        self.item_resetter.on_click(self.trigger_item_reset)

    def define_start_item_selections(self):
        # startvideo selector
        self.startvid = pn.widgets.RadioBoxGroup(
            name="Startvideo",
            options=[
                "Datum",
                self.config["opensearch"]["primary_field"].capitalize(),
                "URL",
                "Text",
            ],
            value="Datum",
        )

        self.startvid.param.watch(self.toggle_start_components, "value")

        # date selector - start
        self.startdate = pn.widgets.DatetimePicker(name="Startdatum", visible=True)

        self.startdate.params = {
            "validator": "_check_date",
            "label": "startdateinput",
            "accessor": "get_items_by_date",
            "has_paging": True,
            "reset_to": None,
        }

        self.startdate.param.watch(self.toggle_start_components, "visible")
        self.startdate.param.watch(
            self.trigger_item_selection, "value", onlychanged=True
        )
        self.controller.register("item_choice", self.startdate)

        # date selector - end
        self.enddate = pn.widgets.DatetimePicker(name="Enddatum", visible=True)
        self.enddate.params = {
            "validator": "_check_date",
            "label": "enddateinput",
            "accessor": "get_items_by_date",
            "has_paging": True,
            "reset_to": None,
        }

        self.enddate.param.watch(self.toggle_start_components, "visible")
        self.enddate.param.watch(self.trigger_item_selection, "value", onlychanged=True)
        self.controller.register("item_choice", self.enddate)

        # crid input
        self.crid_input = pn.widgets.TextInput(
            placeholder=self.config["opensearch"]["primary_field"],
            visible=False,
            max_length=100000,  # TODO: max length adjustment not working, find out how to solve
        )

        self.crid_input.params = {
            "validator": "_check_" + self.config["opensearch"]["primary_field"],
            "accessor": "get_item_by_" + self.config["opensearch"]["primary_field"],
            "label": "cridinput",
            "has_paging": False,
            "reset_to": "",
        }
        self.crid_input.param.watch(self.toggle_start_components, "visible")
        self.crid_input.param.watch(
            self.trigger_item_selection, "value", onlychanged=True
        )
        self.controller.register("item_choice", self.crid_input)

        # url input
        self.url_input = pn.widgets.TextInput(
            name="URL", placeholder="https://", visible=False
        )

        self.url_input.params = {
            "validator": "_check_url",
            "accessor": "get_item_by_url",
            "label": "urlinput",
            "has_paging": False,
            "reset_to": "",
        }

        self.url_input.param.watch(self.toggle_start_components, "visible")
        self.url_input.param.watch(
            self.trigger_item_selection, "value", onlychanged=True
        )
        self.controller.register("item_choice", self.url_input)

        # text input
        self.text_input = pn.widgets.TextAreaInput(
            name="Text",
            placeholder="Text here",
            visible=False,
            max_length=99_999,  # empirical max_length
            rows=5,
            max_rows=10,
            auto_grow=True,
        )

        self.text_input.params = {
            "validator": "_check_text",
            "accessor": "get_item_by_text",  #
            "label": "text_input",  #
            "has_paging": False,
            "reset_to": "",
        }

        self.text_input.param.watch(self.toggle_start_components, "visible")
        self.text_input.param.watch(
            self.trigger_item_selection, "value", onlychanged=True
        )
        self.controller.register("item_choice", self.text_input)

        # all input sources as columns
        self.input_sources = pn.Column(
            self.startvid,
            self.crid_input,
            self.url_input,
            self.text_input,
            self.startdate,
            self.enddate,
        )

    # Filtering block u2c
    def define_reco_filtering_selection_u2c(self):
        self.editorial_choice = pn.widgets.MultiSelect(
            name="Empfehlungen auf Kategorie einschränken",
            options=[],
            visible=True,
            size=4,
        )

        self.editorial_choice.params = {
            "label": "editorialCategories",
            "validator": "_check_editorial_category",
            "reset_to": [],
        }

        self.editorial_choice.options = list(
            filter(
                lambda item: item != "n/a",
                self.controller.get_item_defaults("editorialCategories"),
            )
        )

        user_editorial_watcher = self.editorial_choice.param.watch(
            self.trigger_reco_filter_choice, "value", onlychanged=True
        )

        self.controller.register(
            "reco_filter_u2c",
            self.editorial_choice,
            user_editorial_watcher,
            self.trigger_reco_filter_choice,
        )

        # reset button
        self.reco_resetter_u2c = pn.widgets.Button(
            name="Auswahl zurücksetzen", button_type="primary", margin=10
        )

        self.reco_resetter_u2c.params = {
            "label": "reco_resetter_u2c",
            "resets": ["reco_filter_u2c"],
        }

        self.reco_resetter_u2c.on_click(self.trigger_reco_reset)

    # Filtering blokc c2c
    def define_reco_filtering_selection(self):
        # Select if same, other, mix or custom choice of genre, subgenre, theme and show
        # genre filter selector
        self.genreFilter = pn.widgets.MultiSelect(
            name="Genre-Filterauswahl",
            options={
                "Nur gleiches Genre": "same_genre",
                "Nur andere Genres": "different_genre",
                "Erzählweise auswählen": "choose_erzählweise",
                "Genres auswählen": "choose_genre",
            },
            size=4,
            visible=True,
        )

        self.genreFilter.params = {
            "label": "termfilter_genre",
            "visible_action": ("choose_genre", "genreSelect"),
            "visible_action_2": ("choose_erzählweise", "erzaehlweiseSelect"),
            "reset_to": None,
        }

        genre_watcher = self.genreFilter.param.watch(
            self.trigger_reco_filter_choice, "value", onlychanged=True
        )
        self.controller.register(
            "reco_filter",
            self.genreFilter,
            genre_watcher,
            self.trigger_reco_filter_choice,
        )

        # subgenre filter selector
        self.subgenreFilter = pn.widgets.MultiSelect(
            name="Subgenre-Filterauswahl",
            options={
                "Nur gleiche Subgenres": "same_subgenre",
                "Nur andere Subgenres": "different_subgenre",
                "Inhalt auswählen": "choose_inhalt",
                "Subgenres auswählen": "choose_subgenre",
            },
            size=4,
            visible=True,
        )

        self.subgenreFilter.params = {
            "label": "termfilter_subgenre",
            "visible_action": ("choose_subgenre", "subgenreSelect"),
            "visible_action_2": ("choose_inhalt", "inhaltSelect"),
            "reset_to": None,
        }

        subgenre_watcher = self.subgenreFilter.param.watch(
            self.trigger_reco_filter_choice, "value", onlychanged=True
        )
        self.controller.register(
            "reco_filter",
            self.subgenreFilter,
            subgenre_watcher,
            self.trigger_reco_filter_choice,
        )

        # theme filter selector
        self.themeFilter = pn.widgets.MultiSelect(
            name="Themen-Filterauswahl",
            options={
                "Nur gleiche Themen": "same_theme",
                "Nur andere Themen": "different_theme",
                "Themen auswählen": "choose_theme",
            },
            size=3,
            visible=True,
        )

        self.themeFilter.params = {
            "label": "termfilter_theme",
            "visible_action": ("choose_theme", "themeSelect"),
            "reset_to": None,
        }

        theme_watcher = self.themeFilter.param.watch(
            self.trigger_reco_filter_choice, "value", onlychanged=True
        )
        self.controller.register(
            "reco_filter",
            self.themeFilter,
            theme_watcher,
            self.trigger_reco_filter_choice,
        )

        # show filter selector
        self.showFilter = pn.widgets.MultiSelect(
            name="Sendereihen-Filterauswahl",
            options={
                "Nur gleiche Sendereihe": "same_show",
                "Nur andere Sendereihen": "different_show",
                "Sendereihen auswählen": "choose_show",
            },
            size=3,
            visible=True,
        )

        self.showFilter.params = {
            "label": "termfilter_show",
            "visible_action": ("choose_show", "showSelect"),
            "reset_to": None,
        }

        show_watcher = self.showFilter.param.watch(
            self.trigger_reco_filter_choice, "value", onlychanged=True
        )
        self.controller.register(
            "reco_filter",
            self.showFilter,
            show_watcher,
            self.trigger_reco_filter_choice,
        )

        # Select specific genre, subgenre, theme and show
        # genre selector
        self.erzaehlweiseSelect = pn.widgets.MultiSelect(
            options={
                "Genres Doku": "categories_documentation",
                "Genres Fiktion": "categories_fiction",
                "Genres Show": "categories_show",
                "Genres Information": "categories_information",
                "Genres Live": "categories_live",
            },
            visible=False,
            size=5,
        )

        self.erzaehlweiseSelect.params = {
            "label": "value_erzaehlweiseCategory",
            "reset_to": [],
        }

        erzaehlweise_watcher = self.erzaehlweiseSelect.param.watch(
            self.trigger_reco_filter_choice, "value", onlychanged=True
        )
        self.controller.register(
            "reco_filter",
            self.erzaehlweiseSelect,
            erzaehlweise_watcher,
            self.trigger_reco_filter_choice,
        )

        self.genreSelect = pn.widgets.MultiSelect(
            name="Genre", options=[], visible=False
        )

        self.genreSelect.params = {"label": "value_genreCategory", "reset_to": []}

        self.genreSelect.options = self.controller.get_item_defaults("genreCategory")
        genre_s_watcher = self.genreSelect.param.watch(
            self.trigger_reco_filter_choice, "value", onlychanged=True
        )
        self.controller.register(
            "reco_filter",
            self.genreSelect,
            genre_s_watcher,
            self.trigger_reco_filter_choice,
        )

        # subgenre selector
        self.inhaltSelect = pn.widgets.MultiSelect(
            options={
                "Subgenres Doku": "categories_documentation",
                "Subgenres Fiktion": "categories_fiction",
                "Subgenres Show": "categories_show",
                "Subgenres Information": "categories_information",
                "Subgenres Live": "categories_live",
            },
            visible=False,
            size=5,
        )

        self.inhaltSelect.params = {"label": "value_inhaltCategory", "reset_to": []}

        inhalt_watcher = self.inhaltSelect.param.watch(
            self.trigger_reco_filter_choice, "value", onlychanged=True
        )
        self.controller.register(
            "reco_filter",
            self.inhaltSelect,
            inhalt_watcher,
            self.trigger_reco_filter_choice,
        )

        self.subgenreSelect = pn.widgets.MultiSelect(
            name="Subgenre", options=[], visible=False
        )

        self.subgenreSelect.params = {
            "label": "value_subgenreCategories",
            "reset_to": [],
        }

        self.subgenreSelect.options = self.controller.get_item_defaults(
            "subgenreCategories"
        )
        subgenre_s_watcher = self.subgenreSelect.param.watch(
            self.trigger_reco_filter_choice, "value", onlychanged=True
        )
        self.controller.register(
            "reco_filter",
            self.subgenreSelect,
            subgenre_s_watcher,
            self.trigger_reco_filter_choice,
        )

        # theme selector
        self.themeSelect = pn.widgets.MultiSelect(
            name="Thema", options=[], visible=False
        )

        self.themeSelect.params = {"label": "value_thematicCategories", "reset_to": []}

        self.themeSelect.options = self.controller.get_item_defaults(
            "thematicCategories"
        )
        theme_s_watcher = self.themeSelect.param.watch(
            self.trigger_reco_filter_choice, "value", onlychanged=True
        )
        self.controller.register(
            "reco_filter",
            self.themeSelect,
            theme_s_watcher,
            self.trigger_reco_filter_choice,
        )

        # show selector
        self.showSelect = pn.widgets.MultiSelect(
            name="Sendereihe", options=[], visible=False
        )

        self.showSelect.params = {"label": "value_showTitel", "reset_to": []}

        self.showSelect.options = self.controller.get_item_defaults("showTitle")
        show_s_watcher = self.showSelect.param.watch(
            self.trigger_reco_filter_choice, "value", onlychanged=True
        )
        self.controller.register(
            "reco_filter",
            self.showSelect,
            show_s_watcher,
            self.trigger_reco_filter_choice,
        )

        # combine selections into columns
        self.genre_col = pn.Column(
            self.genreFilter, self.erzaehlweiseSelect, self.genreSelect
        )
        self.subgenre_col = pn.Column(
            self.subgenreFilter, self.inhaltSelect, self.subgenreSelect
        )
        self.theme_col = pn.Column(self.themeFilter, self.themeSelect)
        self.show_col = pn.Column(self.showFilter, self.showSelect)

        # reset button
        self.reco_resetter = pn.widgets.Button(
            name="Auswahl zurücksetzen", button_type="primary", margin=10
        )

        self.reco_resetter.params = {
            "label": "reco_resetter",
            "resets": ["reco_filter", "upper_reco_filter"],
        }

        self.reco_resetter.on_click(self.trigger_reco_reset)

    def define_reco_sorting(self):
        # sorting filter selector
        self.sort = pn.widgets.MultiSelect(
            name="Sortieren", options={"Aktualität": "desc", "Longtail": "asc"}, size=2
        )

        self.sort.params = {"label": "sort_recos", "reset_to": []}
        sort_watcher = self.sort.param.watch(
            self.trigger_item_selection, "value", onlychanged=True
        )
        self.controller.register(
            "reco_filter", self.sort, sort_watcher, self.trigger_item_selection
        )

    def define_reco_duplicate_filtering(self):
        # duplicate filter selector
        self.duplicate = pn.widgets.MultiSelect(
            name="Duplikatfilter",
            options={
                "Doppelte Crid": ["filterDuplicateCrid", "crid"],
                "Identische Description": ["filterDuplicateDescription", "description"],
                "Identische ImageUrl": ["filterDuplicateImageUrl", "teaserimage"],
            },
            size=3,
        )

        self.duplicate.params = {"label": "remove_duplicate", "reset_to": []}

        duplicate_watcher = self.duplicate.param.watch(
            self.trigger_item_selection, "value", onlychanged=True
        )
        self.controller.register(
            "reco_filter",
            self.duplicate,
            duplicate_watcher,
            self.trigger_item_selection,
        )

    def define_reco_incomplete_filtering(self):
        # incomplete filter selector
        self.incompleteSelect = pn.widgets.MultiSelect(
            name="Nur ausgefüllte Daten für:",
            options={"Subgenre": "subgenreCategories", "Thema": "thematicCategories"},
            size=2,
        )

        self.incompleteSelect.params = {"label": "clean_incomplete", "reset_to": []}

        incomplete_watcher = self.incompleteSelect.param.watch(
            self.trigger_reco_filter_choice, "value", onlychanged=True
        )
        self.controller.register(
            "reco_filter",
            self.incompleteSelect,
            incomplete_watcher,
            self.trigger_reco_filter_choice,
        )

    def define_reco_duration_filtering(self):
        gte_values = [2, 5, 10, 15, 30, 45]

        # duration filter selector
        self.duration_filter = pn.widgets.MultiSelect(
            name="Länge-Filter",
            options={
                "Alle": [],
                **{
                    f"ONLY > {minute} Minuten": {"duration": {"gte": minute * 60}}
                    for minute in gte_values
                },
            },
            size=1,
        )

        self.duration_filter.params = {"label": "rangefilter_duration", "reset_to": []}

        duration_filter_watcher = self.duration_filter.param.watch(
            self.trigger_reco_filter_choice, "value", onlychanged=True
        )
        self.controller.register(
            "reco_filter",
            self.duration_filter,
            duration_filter_watcher,
            self.trigger_reco_filter_choice,
        )

    def define_score_threshold(self):
        threshold_values = [
            0.95,
            0.9,
            0.85,
            0.8,
            0.75,
            0.7,
            0.65,
            0.6,
            0.55,
            0.5,
            0.45,
            0.4,
        ]
        # duration filter selector
        self.score_threshold_filter = (
            pn.widgets.MultiSelect(  # TODO: change this to continuous slider
                name="Modell-Score",
                options={
                    "Alle": [],
                    **{
                        f"ONLY SCORE > {score_threshold}": score_threshold
                        for score_threshold in threshold_values
                    },
                },
                size=1,
            )
        )

        self.score_threshold_filter.params = {
            "label": "score_threshold",
            "reset_to": 0.0,
        }

        score_threshold_filter_watcher = self.score_threshold_filter.param.watch(
            self.trigger_reco_filter_choice, "value", onlychanged=True
        )
        self.controller.register(
            "reco_filter",
            self.score_threshold_filter,
            score_threshold_filter_watcher,
            self.trigger_reco_filter_choice,
        )

    def define_user_selections(self):
        self.user_filter_choice = pn.widgets.Select(
            name="Nutzer:in rezipiert in erster Linie", options=[], visible=True, size=4
        )

        self.user_filter_choice.params = {
            "validator": "_check_category",
            "accessor": "get_users_by_category",
            "label": "genre_users",
            "has_paging": True,
            "reset_to": None,
            "active": True,
        }
        self.user_filter_choice.options = self.controller.get_item_defaults(
            "genreCategory"
        )
        user_filter_watcher = self.user_filter_choice.param.watch(
            self.trigger_filter_choice, "value", onlychanged=True
        )
        self.controller.register(
            "user_choice",
            self.user_filter_choice,
            user_filter_watcher,
            self.trigger_filter_choice,
        )

    def define_model_selections(self):
        ## c2c selections
        self.c2c_choice = pn.widgets.MultiSelect(
            name="", options=self.c2c_models, value=self.c2c_model_default
        )
        self.c2c_choice.params = {
            "label": constants.MODEL_CONFIG_C2C,
            "reset_to": self.c2c_model_default,
        }
        model_watcher = self.c2c_choice.param.watch(
            self.trigger_model_choice, "value", onlychanged=True
        )
        self.controller.register(
            "model_choice", self.c2c_choice, model_watcher, self.trigger_model_choice
        )

        ## u2c selections
        self.u2c_model_choice = pn.widgets.MultiSelect(
            name="",
            options=self.u2c_models,
        )
        self.u2c_model_choice.params = {
            "label": constants.MODEL_CONFIG_U2C,
            "reset_to": [],
        }
        model_watcher = self.u2c_model_choice.param.watch(
            self.trigger_model_choice, "value", onlychanged=True
        )
        self.controller.register(
            "model_choice",
            self.u2c_model_choice,
            model_watcher,
            self.trigger_model_choice,
        )

        # reset button
        self.model_resetter = pn.widgets.Button(
            name="Auswahl zurücksetzen", button_type="primary", margin=10
        )

        self.model_resetter.params = {
            "label": "model_resetter",
            "resets": ["model_choice"],
        }

        self.model_resetter.on_click(self.trigger_model_reset)

    def define_page_size(self):
        page_size = self.get_ui_config_value(
            ui_constants.UI_CONFIG_PAGE_SIZE_KEY,
            ui_constants.FALLBACK_UI_PAGE_SIZE_VALUE,
        )
        if isinstance(page_size, int):
            return page_size
        else:
            logger.info(f"{page_size} is not a valid page size. Fallback to default: {ui_constants.FALLBACK_UI_PAGE_SIZE_VALUE}")
            return ui_constants.FALLBACK_UI_PAGE_SIZE_VALUE

    # event handling
    async def trigger_reco_filter_choice(self, event):
        logger.info(event)
        self.toggle_visibility(event)
        await self.get_items_with_parameters()

    async def trigger_item_pagination(self, event):
        logger.info(event)
        if event.obj.name == ui_constants.DOWN_ARROW:
            self.controller.increase_page_number()
        elif event.obj.name == ui_constants.UP_ARROW:
            self.controller.decrease_page_number()
        await self.get_items_with_parameters()
        self.disablePageButtons()

    async def trigger_filter_choice(self, event):
        logger.info(event)
        self.controller.reset_page_number()
        self.disablePageButtons()
        await self.get_items_with_parameters()

    async def trigger_model_choice(self, event):
        if self.model_choice.active[0] == 0:
            self.controller.reset_component(
                "model_choice", constants.MODEL_CONFIG_U2C, []
            )
        elif self.model_choice.active[0] == 1:
            self.controller.reset_component(
                "model_choice", constants.MODEL_CONFIG_C2C, []
            )
        await self.trigger_filter_choice(event)

    async def trigger_item_selection(self, event):
        # if the "new" parameter of the event contains a string, load that string
        logger.info(event)
        if event.new:
            await self.get_items_with_parameters()
            self.pagination[4] = self.controller.get_num_pages()
        else:
            self.main_content[:] = []
            self.floating_elements = []
        self.controller.reset_page_number()
        self.disablePageButtons()

    def trigger_item_reset(self, event):
        logger.info(event)
        self.main_content[:] = []
        self.floating_elements.objects = []
        self.controller.reset_defaults(event.obj.params["resets"])
        self.controller.reset_page_number()
        self.draw_pagination()

    async def trigger_reco_reset(self, event):
        logger.info(event)
        self.controller.reset_defaults(event.obj.params["resets"])
        self.controller.reset_page_number()
        await self.get_items_with_parameters()

    def trigger_model_reset(self, event):
        self.model_choice.active = [0]
        self.trigger_item_reset(event)

    def trigger_modal(self, event):
        logger.info(event)
        item = event.obj.params["item"]
        button = event.obj.params["button"]

        if button == "history_button":
            title = "Nutzungshistorie von [" + item.id + "]"
            item_dto = dto_from_classname(
                "HistoryItemDto",
                constants.ITEM_POSITION_START,
                constants.ITEM_TYPE_CONTENT,
                constants.ITEM_PROVENANCE_C2C,
            )
            items = self.controller.get_items_by_field(item_dto, item.history)
            item_row_1 = pn.Row()
            item_row_2 = pn.Row()
            for idx, item_dto in enumerate(items):
                card = self.controller.get_item_viewer(item_dto)
                if idx < 5:
                    item_row_1.append(card.draw(item_dto, idx + 1, "mediathek"))
                else:
                    item_row_2.append(card.draw(item_dto, idx + 1, "mediathek"))
            config = {"headerControls": "closeonly xs", "position": "center"}
            floatpanel = pn.layout.FloatPanel(
                item_row_1,
                item_row_2,
                name=title,
                margin=2,
                config=config,
                height=500,
                width=1500,
                contained=False,
            )
            self.floating_elements.append(floatpanel)

        if button == "params_button":
            title = "Model Parameters - " + self.u2c_model_choice.value[0] + ""
            params_dto = dto_from_classname(
                "ModelParametersDto",
                constants.ITEM_POSITION_START,
                constants.ITEM_TYPE_CONTENT,
                constants.ITEM_PROVENANCE_C2C,
            )
            card = self.controller.get_item_viewer(params_dto)
            model_params = self.controller.get_model_params()
            item_row = card.draw(model_params)
            config = {"headerControls": "closeonly xs", "position": "center"}
            floatpanel = pn.layout.FloatPanel(
                item_row, name=title, margin=2, config=config, contained=False
            )
            self.floating_elements.append(floatpanel)

    # toggling ui components

    def toggle_start_components(self, event):
        logger.info(event)
        # disable a component depending on the value of another component
        if event.obj.name == "Startvideo" and event.new == "Datum":
            self.startdate.visible = self.enddate.visible = self.genreRadio.visible = (
                self.erzaehlweise.visible
            ) = self.subgenreRadio.visible = self.inhalt.visible = (
                self.themes.visible
            ) = self.shows.visible = True
            self.crid_input.visible = self.url_input.visible = (
                self.text_input.visible
            ) = False
            self.crid_input.value = self.url_input.value = ""
        elif (
            event.obj.name == "Startvideo"
            and event.new == self.config["opensearch"]["primary_field"].capitalize()
        ):
            self.startdate.visible = self.enddate.visible = self.url_input.visible = (
                self.genreRadio.visible
            ) = self.erzaehlweise.visible = self.genres.visible = (
                self.subgenreRadio.visible
            ) = self.inhalt.visible = self.subgenres.visible = self.themes.visible = (
                self.shows.visible
            ) = self.text_input.visible = False
            self.crid_input.visible = True
            self.url_input.value = ""
        elif event.obj.name == "Startvideo" and event.new == "URL":
            self.startdate.visible = self.enddate.visible = self.crid_input.visible = (
                self.genreRadio.visible
            ) = self.erzaehlweise.visible = self.genres.visible = (
                self.subgenreRadio.visible
            ) = self.inhalt.visible = self.subgenres.visible = self.themes.visible = (
                self.shows.visible
            ) = self.text_input.visible = False
            self.crid_input.value = ""
            self.url_input.visible = True
        elif event.obj.name == "Startvideo" and event.new == "Text":
            self.startdate.visible = self.enddate.visible = self.crid_input.visible = (
                self.genreRadio.visible
            ) = self.erzaehlweise.visible = self.genres.visible = (
                self.subgenreRadio.visible
            ) = self.inhalt.visible = self.subgenres.visible = self.themes.visible = (
                self.shows.visible
            ) = self.url_input.visible = False
            self.crid_input.value = ""
            self.text_input.visible = True
        # shorten this, either combine last two elifs or with dict of widget groups

    def toggle_model_choice(self, event):
        logger.info(event)
        active_block = event.obj.active[0]
        self.put_navigational_block(2, self.source_block[active_block])
        if active_block == 0:
            self.put_navigational_block(3, self.filter_block[0])
        else:
            self.put_navigational_block(3, self.filter_block[1])
        self.assemble_navigation_elements()

    def toggle_client_choice(self, event):
        logger.info(event)
        self.client = event.obj.value
        pn.state.location.update_query(client=self.client)
        # await this call?
        pn.state.location.reload = True

    def toggle_user_choice(self, event):
        active_component = event.obj.objects[event.obj.active[0]]
        for component in self.controller.components["user_choice"].values():
            if component.params["label"] != active_component.params["label"]:
                component.params["active"] = False
            else:
                component.params["active"] = True

    def toggle_genre_selection_by_upper_genre(self, event):
        logger.info(event)
        if (
            event.obj.params["label"] == "erzaehlweiseCategory"
            or event.obj.params["label"] == "value_erzaehlweiseCategory"
        ):
            category = "genres"
            if event.obj.params["label"] == "erzaehlweiseCategory":
                upper_category = self.erzaehlweise
                widget = self.genres
        elif (
            event.obj.params["label"] == "inhaltCategory"
            or event.obj.params["label"] == "value_inhaltCategory"
        ):
            category = "subgenres"
            if event.obj.params["label"] == "inhaltCategory":
                upper_category = self.inhalt
                widget = self.subgenres
        if event.type == "changed":
            widget.value = self.controller.get_genres_and_subgenres_from_upper_category(
                upper_category.value, category
            )

    def toggle_visibility(self, event):
        for action in ["visible_action", "visible_action_2"]:
            if event.type == "changed" and event.obj.params.get(action, False):
                value_trigger, on_component = event.obj.params[action]
                component = getattr(self, on_component)
                new_event = event.new

                if value_trigger == new_event[0]:
                    component.visible = True
                else:
                    component.visible = False

        if event.obj.params["label"] == "erzählweiseGenreRadio":
            self.erzaehlweise.value = []
        elif event.obj.params["label"] == "inhaltSubgenreRadio":
            self.inhalt.value = []
        elif event.obj.params["label"] == "filer_genre":
            self.erzaehlweiseSelect.value = []
        elif event.obj.params["label"] == "filter_subgenre":
            self.inhaltSelect.value = []

    def disablePageButtons(self):
        self.previousPage.disabled = self.controller.get_page_number() == 1
        self.nextPage.disabled = (
            self.controller.get_page_number() == self.controller.get_num_pages()
        )

    # assembly & rendering

    def draw_pagination(self):
        if not self.main_content.objects:
            from_page = " - "
            to_page = " - "
        else:
            from_page = self.controller.get_page_number()
            to_page = self.controller.get_num_pages()

        self.pagination[2] = pn.pane.Markdown(f"""### { from_page }""")
        self.pagination[4] = pn.pane.Markdown(f"""### { to_page } """)

    def put_navigational_block(self, position, block):
        self.navigational_components[position] = block

    def assemble_navigation_elements(self):
        self.nav_controls.clear()
        for block in self.navigational_components.values():
            for component in block:
                self.nav_controls.append(component)
            self.nav_controls.append(pn.layout.Divider())

    def update_widgets_from_url_parameter(self):
        """
        Gets called by onload and iterate over dictionary: {Key: <parameter_name_from_config> Value: <widget_from_config>, ...}
        Inserts values from given parameter names from url into given widgets, parameter names in Key prevent one parameter name for multiple widgets
        """
        for parameter_name, widget in self.url_parameter_text_field_mapping.items():
            parameter_value_str = pn.state.location.query_params.get(
                parameter_name, None
            )
            if parameter_value_str is not None:
                try:
                    parameter_value = int(parameter_value_str)
                    parameter_value = str(parameter_value)
                except ValueError:
                    parameter_value = parameter_value_str
                widget.value = parameter_value

    def get_ui_config_value(self, key, fallback):
        """
        Gets a config one level under ui_config from config yaml

        Args:
            key (string): key of config you want to load
            fallback (string): fallback value if given key can not be found under ui_config

        Returns:
            config: config of key given or fallback value if key is not present under ui_config
        """
        return self.config.get(ui_constants.UI_CONFIG_KEY + "." + key, fallback)

    def build_common_ui_widget_dispatcher(
        self, common_ui_widget_type: str, common_ui_widget_config: dict[str, Any]
    ):
        """
        Decides which common ui widget should be build based on the given ui type. If no type matches returns None

        Args:
            common_ui_widget_type (string): A common ui component type. Can contain: text field and multi select
            common_ui_widget_config(config): config of a common ui widget type

        Returns:
            widget of common ui widget type, built based on given config
        """
        if common_ui_widget_type == ui_constants.RADIO_BOX_TYPE_VALUE:
            radio_box_widget = RadioBoxWidget(self, self.controller)
            return radio_box_widget.create(common_ui_widget_config)
        else:
            widget = self.widgets.get(common_ui_widget_type)
            if not widget:
                return None
            return widget.create(common_ui_widget_config)

    def build_widgets(self, widgets_config):
        """
        Creates a list of ui widgets based on the given config. Every widget has  a type and based on that, it gets built

        Args:
            widgets_config (config): configs of ui widgets

        Returns:
            widgets_list (list): list of ui widgets
        """
        widgets_list = []
        if widgets_config is not None:
            for widget_config in widgets_config:
                component_type = widget_config.get(ui_constants.WIDGET_TYPE_KEY, "")
                component_from_dispatcher = self.build_common_ui_widget_dispatcher(
                    component_type, widget_config
                )
                if component_from_dispatcher is not None:
                    widgets_list.append(component_from_dispatcher)
                elif ui_constants.ACCORDION_TYPE_VALUE == component_type:
                    widgets_list.append(
                        self.widgets[ui_constants.ACCORDION_TYPE_VALUE].create(
                            widget_config
                        )
                    )
                    if widget_config.get(ui_constants.ACCORDION_RESET_BUTTON_KEY):
                        widgets_list.append(
                            (
                                self.widgets[
                                    ui_constants.ACCORDION_TYPE_VALUE
                                ].create_accordion_reset_buttons(widget_config)
                            )
                        )
                elif "radio_box" == component_type:
                    widgets_list.append(
                        self.widgets[ui_constants.RADIO_BOX_TYPE_VALUE].create(
                            widget_config
                        )
                    )
                else:
                    logger.error("Unknown UI Config Type: " + component_type)
        else:
            logger.error(
                "No UI Widgets are defined in Config File, or key name is wrong"
            )

        return widgets_list

    def build_blocks(self):
        """
        Creates a list of ui blocks based on the given config. Every block has a label and contains a list of ui widgets

        Returns:
            block_list (list): list of ui blocks
        """
        block_list = []
        blocks_config = self.config[ui_constants.UI_CONFIG_BLOCKS]
        for block_config in blocks_config:
            list_of_widgets_in_block = self.build_widgets(
                block_config.get(ui_constants.BLOCK_CONFIG_WIDGETS_KEY)
            )
            if block_config.get("show_reset_button", True):
                list_of_widgets_in_block.append(
                    ResetButtonWidget(self, self.controller).create(
                        list_of_widgets_in_block
                    )
                )
            block = {
                ui_constants.BLOCK_LABEL_LIST_KEY: block_config.get(
                    ui_constants.BLOCK_CONFIG_LABEL_KEY,
                    ui_constants.FALLBACK_BLOCK_LABEL_VALUE,
                ),
                ui_constants.BLOCK_WIDGETS_LIST_KEY: list_of_widgets_in_block,
            }
            block_list.append(block)
        return block_list

    def append_block_to_navigation(self, block):
        """
        Adds ui block with label (headline) which contains all ui widgets from config yaml to config_based_nav_controls list
        config_based_nav_controls is then used to render the sidebar

        Args:
            block (block): a ui block which is configured in config yaml and contains widgets
        """
        self.config_based_nav_controls.append(
            "### " + block.get(ui_constants.BLOCK_LABEL_LIST_KEY)
        )
        for block_component in block.get(ui_constants.BLOCK_WIDGETS_LIST_KEY):
            self.config_based_nav_controls.append(block_component)

    def assemble_components(self):
        accordion_max_width = ui_constants.ACCORDION_MAX_WIDTH
        if ui_constants.UI_CONFIG_BLOCKS in self.config:
            blocks = self.build_blocks()
            logger.debug("found blocks %s", blocks)
            block_counts = len(blocks)
            # Client
            client_title = pn.pane.Markdown("### Mandant wählen")
            client_choice = pn.widgets.RadioBoxGroup(
                name="Client",
                options=get_client_options(self.config_full_paths),
                value=self.client,
            )

            if self.client_choice_visibility:
                self.config_based_nav_controls.append(client_title)
                client_choice.param.watch(
                    self.toggle_client_choice, "value", onlychanged=True
                )
                self.config_based_nav_controls.append(client_choice)

            for index, block in enumerate(blocks):
                self.append_block_to_navigation(block)
                # append a divider if its not the last block
                if index + 1 != block_counts:
                    self.config_based_nav_controls.append(pn.layout.Divider())

        else:
            # Client
            client_title = pn.pane.Markdown("### Mandant wählen")
            self.client_choice = pn.widgets.RadioBoxGroup(
                name="Client",
                options=get_client_options(self.config_full_paths),
                value=self.client,
            )

            if self.client_choice_visibility:
                self.put_navigational_block(
                    0, ["### Mandant wählen", self.client_choice]
                )
                self.client_choice.param.watch(
                    self.toggle_client_choice, "value", onlychanged=True
                )

            # Models
            if (
                constants.MODEL_CONFIG_U2C in self.config
            ):  # TODO: refactor bootstrapping of application to make this more generic
                self.model_choice = pn.Accordion(
                    ("Content-2-Content", self.c2c_choice),
                    ("User-2-Content", self.u2c_model_choice),
                )
            else:
                self.model_choice = pn.Accordion(("Content-2-Content", self.c2c_choice))

            self.model_choice.active = [0]
            self.model_choice.toggle = True
            self.model_choice.max_width = accordion_max_width

            self.put_navigational_block(
                1, ["### Modelle wählen", self.model_choice, self.model_resetter]
            )
            self.model_choice.param.watch(
                self.toggle_model_choice, "active", onlychanged=True
            )

            # Item source
            self.item_source = pn.Accordion(
                ("Quelle wählen", self.input_sources),
                ("Genre wählen", self.genre_start_col),
                ("Subgenre wählen", self.subgenre_start_col),
                ("Thema wählen", self.themes),
                ("Sendereihe wählen", self.shows),
            )
            self.item_source.active = [0]
            self.item_source.max_width = accordion_max_width

            # User source
            self.user_source = pn.Accordion(("User-Filter", self.user_filter_choice))
            #            self.user_source.active = [1,1]
            self.user_source.toggle = False
            self.user_source.max_width = accordion_max_width
            self.user_source.param.watch(
                self.toggle_user_choice, "active", onlychanged=True
            )

            self.source_block = {}
            self.source_block[0] = [
                "### Start-Video bestimmen",
                self.item_source,
                self.item_resetter,
            ]
            self.source_block[1] = [
                "### Start-User bestimmen",
                self.user_source,
                self.item_resetter,
            ]

            self.put_navigational_block(2, self.source_block[0])

            # Postprocessing and Filtering
            self.reco_items = pn.Accordion(
                ("Modell-Score", self.score_threshold_filter),
                ("Duplikatfilterung", self.duplicate),
                ("Sortierung", self.sort),
                ("Fehlende Daten ausblenden", self.incompleteSelect),
                ("Länge-Filter", self.duration_filter),
                ("Genre-Filter", self.genre_col),
                ("Subgenre-Filter", self.subgenre_col),
                ("Themen-Filter", self.theme_col),
                ("Sendereihe-Filter", self.show_col),
            )
            self.reco_items.max_width = accordion_max_width

            # Postprocessing and Filtering U2C
            self.reco_items_u2c = pn.Accordion(
                ("Editorial-Categories", self.editorial_choice)
            )
            self.reco_items_u2c.max_width = accordion_max_width

            self.filter_block = {}
            self.filter_block[0] = [
                "### Empfehlungen beeinflussen",
                self.reco_items,
                self.reco_resetter,
            ]
            self.filter_block[1] = [
                "### Empfehlungen beeinflussen",
                self.reco_items_u2c,
                self.reco_resetter_u2c,
            ]

            self.put_navigational_block(3, self.filter_block[0])
            self.assemble_navigation_elements()

        # empty screen hinweis
        self.main_content.append(
            pn.pane.Alert(
                "Wähle ein oder mehrere Modelle, sowie ein Start-Item oder -User",
                alert_type="warning",
            )
        )

        # previous button
        self.previousPage = pn.widgets.Button(
            name=ui_constants.UP_ARROW,
            button_type="primary",
            margin=10,
            width=50,
            disabled=True,
        )
        self.previousPage.on_click(self.trigger_item_pagination)
        self.pagination.append(self.previousPage)

        self.pagination.append(pn.pane.Markdown("""### Seite """))
        self.pagination.append(pn.pane.Markdown("""### - """))
        self.pagination.append(pn.pane.Markdown("""### von """))
        self.pagination.append(pn.pane.Markdown("""### - """))

        # next button
        self.nextPage = pn.widgets.Button(
            name=ui_constants.DOWN_ARROW,
            button_type="primary",
            width=50,
            margin=10,
            disabled=True,
        )
        self.nextPage.on_click(self.trigger_item_pagination)
        self.pagination.append(self.nextPage)

    def get_version_information_and_append_to_sidebar(self, sidebar):
        """
        Method to get version information and append it to the sidebar.
        Only used in version information in config. Gets added to config by
        deployment pipeline.

        :param sidebar: The sidebar to append the version information.
        :return: The updated sidebar.
        """
        deployment_version_info = self.config.get("deployment_version_info")
        if deployment_version_info:
            version_widget = pn.pane.Markdown(deployment_version_info)
            sidebar.append(pn.layout.Divider())
            sidebar.append(version_widget)
        return sidebar

    #

    async def get_items_with_parameters(self):
        """
        Calls the actual search function in controller to get results for query
        """
        self.main_content[:] = []

        try:
            models, items, config = await asyncio.to_thread(self.controller.get_items)
            for idx, row in enumerate(items):
                self.add_cards_row(models, config, idx, row)
                self.draw_pagination()

        except (EmptySearchError, ModelValidationError) as e:
            self.main_content.append(pn.pane.Alert(str(e), alert_type="warning"))
        except DateValidationError as e:
            logger.info(str(e))
        except Exception as e:
            self.main_content.append(pn.pane.Alert(str(e), alert_type="danger"))
            logger.warning(traceback.print_exc())
        self.disablePageButtons()

    def add_cards_row(self, models: list[any], config: str, idx: int, row: list[any]):
        """

        """
        start_card = None
        reco_cards = []
        for idz, item_dto in enumerate(row):
            card = self.controller.get_item_viewer(item_dto, self)
            if (
                    self.controller.get_display_mode()
                    == constants.DISPLAY_MODE_SINGLE
            ):
                displayed_card = card.draw(
                    item_dto, idz, models[0], config, self.trigger_modal
                )
            else:
                displayed_card = card.draw(
                    item_dto, idz, models[idx], config, self.trigger_modal
                )
            if idz == 0:
                start_card = displayed_card
            else:
                reco_cards.append(displayed_card)

        cards_row = pn.Row(start_card, *reco_cards[:self.page_size])
        row_with_navigation_buttons = self.create_navigation_elements_for_cards_row(cards_row, start_card, reco_cards)
        self.main_content.append(pn.Row(pn.Column(cards_row, row_with_navigation_buttons)))

    def create_navigation_elements_for_cards_row(self, cards_row: pn.Row, start_card: pn.layout.card.Card, reco_cards: list) -> pn.Row:
        """
        :param cards_row: pn.Row, the parent row containing the card elements to navigate through
        :param start_card: pn.layout.card.Card, the card element at the start
        :param reco_cards: list, list of recommended card elements
        :return: pn.Row, row with navigation buttons for navigating through the cards
        """
        prev_button = pn.widgets.Button(name=f"{ui_constants.LEFT_ARROW}", width=100)
        prev_button.disabled = True
        next_button = pn.widgets.Button(name=f"{ui_constants.RIGHT_ARROW}", width=100)
        row_with_navigation_buttons = pn.Row(
            prev_button,
            pn.Spacer(),
            next_button,
        )

        widgets_in_row = {
            "cards_row": cards_row,
            "start_card": start_card,
            "reco_cards": reco_cards,
            "page_size": self.page_size,
            "prev_button": prev_button,
            "next_button": next_button,
        }

        prev_button.on_click(functools.partial(self._update_prev, widgets=widgets_in_row))
        next_button.on_click(functools.partial(self._update_next, widgets=widgets_in_row))

        return row_with_navigation_buttons

    def _update_next(self, event, widgets: dict[any]):
        """
        :param event: Event that triggers the update
        :param widgets: Dictionary containing widgets to be updated
        :return: None

        This method updates the next page of cards based on the current page size. If the page size is smaller than the length
        of the cards list, it adjusts the page size and updates the cards to display the next set of cards. Finally, it toggles
        the 'next_button' and 'prev_button' widgets based on the new page size.
        """
        if widgets['page_size'] < len(widgets['reco_cards']):
            widgets['page_size'] += self.page_size
            widgets['cards_row'].objects = [
                widgets['start_card'],
                *widgets['reco_cards'][widgets['page_size'] - self.page_size:widgets['page_size']]
            ]
        widgets['prev_button'].disabled = False
        widgets['next_button'].disabled = (widgets['page_size'] + self.page_size) > len(widgets['reco_cards'])

    def _update_prev(self, event, widgets: dict[any]):
        """
        :param event: Event that triggers the update
        :param widgets: Dictionary containing widgets to be updated
        :return: None

        This method updates the previous page of cards based on the current page size. If the page size is greater than the stored
        page size, it adjusts the page size and updates the cards to display the previous set of cards. Finally, it toggles the
        'next_button' and 'prev_button' widgets based on the new page size.
        """
        if widgets['page_size'] > self.page_size:
            widgets['page_size'] -= self.page_size
            widgets['cards_row'].objects = [
                widgets['start_card'],
                *widgets['reco_cards'][widgets['page_size'] - self.page_size:widgets['page_size']]
            ]
        widgets['next_button'].disabled = False
        widgets['prev_button'].disabled = widgets['page_size'] <= self.page_size

    @staticmethod
    def render_404():
        return pn.pane.Markdown("""## Unknown location""")

    def render(self):
        logger.info("assemble components")
        self.assemble_components()
        logger.debug("assemble components done")

        title = self.get_ui_config_value(
            ui_constants.UI_CONFIG_TITLE_KEY,
            ui_constants.FALLBACK_UI_CONFIG_TITLE_VALUE,
        )
        logo = self.get_ui_config_value(
            ui_constants.UI_CONFIG_LOGO_KEY, ui_constants.FALLBACK_UI_CONFIG_LOGO_VALUE
        )
        header_background = self.get_ui_config_value(
            ui_constants.UI_CONFIG_HEADER_BACKGROUND_COLOR_KEY,
            ui_constants.FALLBACK_UI_CONFIG_BACKGROUND_COLOR_VALUE,
        )

        pn.config.raw_css.append(
            self.get_ui_config_value(ui_constants.UI_CONFIG_CUSTOM_CSS_KEY, "")
        )

        # Decide which sidebar to use, if config_based is available prefer this
        if len(self.config_based_nav_controls) == 0:
            sidebar = self.nav_controls
        else:
            sidebar = self.config_based_nav_controls

        sidebar = self.get_version_information_and_append_to_sidebar(sidebar)

        # finally add onload, check if url parameter are defined in config and link to widgets
        pn.state.onload(self.update_widgets_from_url_parameter)

        self.template = pn.template.BootstrapTemplate(
            site_url="./",
            title=title,
            logo=logo,
            sidebar=[sidebar],
            main=[self.floating_elements, self.main_content, self.pagination],
            header_background=header_background,
        )

        return self.template
