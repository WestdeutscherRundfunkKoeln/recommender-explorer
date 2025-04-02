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
from util.ui_utils import retrieve_default_model_accordion
from util.dto_utils import dto_from_classname
from util.file_utils import (
    get_client_options,
)
from view import ui_constants
from view.widgets.accordion_widget import AccordionWidget, AccordionWidgetWithCards
from view.widgets.date_time_picker_widget import DateTimePickerWidget
from view.widgets.date_time_quick_select_widget import DateTimeQuickSelectWidget
from view.widgets.multi_select_widget import MultiSelectionWidget
from view.widgets.radio_box_widget import RadioBoxWidget
from view.widgets.reset_button import ResetButtonWidget
from view.widgets.slider_widget import SliderWidget
from view.widgets.text_area_input_widget import TextAreaInputWidget
from view.widgets.text_field_widget import TextFieldWidget
from view.widgets.refinement_widget import RefinementWidget

from view.widgets.widget import UIWidget

# loggin preference
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
formatter = logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

#
# Main App
#
class RecoExplorerApp:
    __in_flight_counter = 0

    def __init__(
        self, config_full_paths: dict[str, str], config: dict[str, Any], client: str
    ) -> None:
        # basic setup
        self.config = config
        self.client = client
        self.config_full_paths = config_full_paths
        self.config_full_path = config_full_paths[client]
        self.controller = RecommendationController(self.config)

        self.widgets = {
            ui_constants.REFINEMENT_WIDGET_TYPE_VALUE: RefinementWidget(
                self, self.controller
            ),
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
        self.navigational_components = {}
        self.config_based_nav_controls = pn.WidgetBox()
        self.client_choice_visibility = len(self.config_full_paths) > 1

        #
        self.define_item_pagination()

        self.template = pn.template.BootstrapTemplate()
        self.main_content = pn.Column()
        self.page_size = self.define_page_size()

        # init some of the component values
        self.set_c2c_model_definitions()
        self.set_u2c_model_definitions()

        self.url_parameter_text_field_mapping = {}

        # stores the UI elements to avoid building them when the states changes
        block_list2 = []
        choosen_accordion = None

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
        self.pagination_top = pn.Row()
        self.pagination = pn.Row()
        self.floating_elements = pn.Row(height=0, width=0)

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
            logger.info(
                f"{page_size} is not a valid page size. Fallback to default: {ui_constants.FALLBACK_UI_PAGE_SIZE_VALUE}"
            )
            return ui_constants.FALLBACK_UI_PAGE_SIZE_VALUE

    # event handling
    async def trigger_reco_filter_choice(self, event):
        logger.info(event)
        self.toggle_visibility(event)
        await self.get_items_with_parameters()

    async def trigger_item_pagination(self, event):
        logger.info(event)
        if event.obj.name == ui_constants.RIGHT_ARROW:
            self.controller.increase_page_number()
        elif event.obj.name == ui_constants.LEFT_ARROW:
            self.controller.decrease_page_number()
        await self.get_items_with_parameters()
        self.disablePageButtons()

    async def trigger_filter_choice(self, event):
        logger.info(event)
        self.controller.reset_page_number()
        self.disablePageButtons()
        await self.get_items_with_parameters()

    async def trigger_model_choice(self, event):
        logger.info(event)
        global choosen_accordion
        if choosen_accordion == "0":
            self.controller.reset_component(
                "model_choice", constants.MODEL_CONFIG_U2C, []
            )
        elif choosen_accordion == "1":
            self.controller.reset_component(
                "model_choice", constants.MODEL_CONFIG_C2C, []
            )
        self.controller.reset_page_number()
        self.disablePageButtons()
        await self.get_items_with_parameters()

    async def trigger_model_choice_new(self, event):
        logger.info(event)
        self.controller.reset_page_number()
        self.disablePageButtons()
        await self.get_items_with_parameters()

    async def trigger_user_cluster_choice(self, event):
        logger.info(event)
        self.controller.reset_page_number()
        self.disablePageButtons()
        await self.get_items_with_parameters()

    async def trigger_user_filter_choice(self, event):
        logger.info(event)
        self.controller.reset_page_number()
        self.disablePageButtons()
        await self.get_items_with_parameters()

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

        self.pagination[2] = pn.pane.Markdown(f"""### {from_page}""")
        self.pagination[4] = pn.pane.Markdown(f"""### {to_page} """)

    def put_navigational_block(self, position, block):
        self.navigational_components[position] = block

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
        self, common_ui_widget_type: str, common_ui_widget_config: dict[str, Any]):
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

        elif common_ui_widget_type == ui_constants.REFINEMENT_WIDGET_TYPE_VALUE:
             refinement_widget = RefinementWidget(self, self.controller)
             return refinement_widget.create()

        else:
            widget = self.widgets.get(common_ui_widget_type)
            if not widget:
                return None
            return widget.create(common_ui_widget_config)

    def build_widgets(self, widgets_config):
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
                    accordion_widget = self.widgets[ui_constants.ACCORDION_TYPE_VALUE].create(widget_config)
                    widgets_list.append(accordion_widget)

            if widget_config.get(ui_constants.ACCORDION_RESET_BUTTON_KEY):
                widgets_list.append(
                    self.widgets[ui_constants.ACCORDION_TYPE_VALUE].create_accordion_reset_buttons(
                        widget_config)
                )

            else:
                logger.error("UI Config Type: " + component_type)

        else:
            logger.error("No UI Widgets are defined in Config File, or key name is wrong")


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
                ui_constants.BLOCKS_CONFIG_LINKTO: block_config.get(
                    ui_constants.BLOCKS_CONFIG_LINKTO
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

    def build_ui(self):
        # clear the nav controls
        self.config_based_nav_controls.clear()

        # Client
        client_title = pn.pane.Markdown("### Mandant wählen")
        client_choice = pn.widgets.RadioBoxGroup(
            name="Client",
            options=get_client_options(self.config_full_paths),
            value=self.client,
            sizing_mode="scale_width",
        )

        if self.client_choice_visibility:
            self.config_based_nav_controls.append(client_title)
            client_choice.param.watch(
                self.toggle_client_choice, "value", onlychanged=True
            )
            self.config_based_nav_controls.append(client_choice)

    def add_blocks_to_navigation(self, ActiveAccordion: str = ""):
        blocks_config = self.config[ui_constants.UI_CONFIG_BLOCKS]
        global block_list2
        global choosen_accordion

        # decide if this function was called by an accordion_with_cards widget or by the assembly function
        if ActiveAccordion == "":
            blocks = self.build_blocks()
            block_list2 = blocks
            choosen_accordion = retrieve_default_model_accordion(self.config["ui_config"])

        # then it's an index sent by the accordion_widget class
        if ActiveAccordion != "":
            choosen_accordion = ActiveAccordion
            self.build_ui() #reset the nav bar before doing modifications

        # Create a dictionary to group blocks by their linkto value
        grouped_blocks = {}
        # To store blocks without 'linkto'
        no_linkto_blocks = []

        # Iterate through the blocks_config configurations
        for block_config in blocks_config:
            # Get the 'linkto' value if it exists
            linkto_value = block_config.get(ui_constants.BLOCKS_CONFIG_LINKTO)

            # Check if the block has a 'linkto' value
            if linkto_value:
                if linkto_value not in grouped_blocks:
                    grouped_blocks[linkto_value] = []

                # Get the label of that accordion
                Acc_label = block_config.get(ui_constants.BLOCK_LABEL_LIST_KEY)

                # Find the corresponding block from the blocks list
                corresponding_blocks = [
                    block
                    for block in block_list2
                    if block.get("label") == Acc_label
                    and block.get("linkto") == linkto_value
                ]

                # Append the corresponding blocks to the group
                grouped_blocks[linkto_value].extend(corresponding_blocks)
            else:
                # If no 'linkto' is found, store the block in no_linkto_blocks
                corresponding_blocks = [
                    block
                    for block in block_list2
                    if block.get("label") == block_config["label"]
                ]
                no_linkto_blocks.extend(corresponding_blocks)

        if grouped_blocks:
            choosen_blocks = grouped_blocks.get(choosen_accordion, [])
            all_blocks_to_add = no_linkto_blocks + choosen_blocks

        else:
            all_blocks_to_add = no_linkto_blocks

        # Append blocks to the navigation in the original order
        for index, block in enumerate(block_list2):
            # Check if the block is either in the no_linkto_blocks or the first_group_blocks
            if block in all_blocks_to_add:
                self.append_block_to_navigation(block)
                # Append a divider if it's not the last block
                if index + 1 != len(block_list2):
                    self.config_based_nav_controls.append(pn.layout.Divider())

    def assemble_components(self):
        accordion_max_width = ui_constants.ACCORDION_MAX_WIDTH
        if ui_constants.UI_CONFIG_BLOCKS in self.config:
            # build client choice
            self.build_ui()

            # check if particular blocks belong to another ones and then populate the navigation
            self.add_blocks_to_navigation()

            # empty screen hinweis
            self.NoModelChossen = pn.pane.Alert(
                "Wähle ein oder mehrere Modelle, sowie ein Start-Item oder -User",
                alert_type="warning",
            )

            self.pagination_top.append(self.NoModelChossen)

            # previous button
            self.previousPage = pn.widgets.Button(
                name= ui_constants.LEFT_ARROW,
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
                name= ui_constants.RIGHT_ARROW,
                button_type="primary",
                width=50,
                margin=10,
                disabled=True,
            )
            self.nextPage.on_click(self.trigger_item_pagination)
            self.pagination.append(self.nextPage)

        ## In case no config file was given
        else:
            # empty screen hinweis
            self.NoConfig = pn.pane.Alert(
                "Couldn't find a Config file",
                alert_type="warning",
            )
            self.pagination.append(self.NoConfig)

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

    async def get_items_with_parameters(self):
        """
        Calls the actual search function in controller to get results for query
        """
        self.main_content[:] = [
            pn.Row(
                pn.indicators.LoadingSpinner(
                    value=True,
                    width=25,
                    height=25,
                    align="center",
                    margin=(5, 0, 5, 10),
                )
            )
        ]
        self.pagination_top[:] = []

        self.__in_flight_counter += 1
        try:
            models, items, config = await asyncio.to_thread(self.controller.get_items)

        except (EmptySearchError, ModelValidationError) as e:
            self.main_content.append(pn.pane.Alert(str(e), alert_type="warning"))
            return
        except DateValidationError as e:
            logger.info(str(e))
            return
        except Exception as e:
            self.main_content.append(pn.pane.Alert(str(e), alert_type="danger"))
            logger.warning(traceback.print_exc())
            return
        finally:
            self.__in_flight_counter -= 1

        if self.__in_flight_counter:
            return

        self.main_content[:] = [
            self.add_cards_row(models, config, idx, row)
            for idx, row in enumerate(items)
        ]
        self.draw_pagination()
        self.disablePageButtons()

    def add_cards_row(
        self, models: list[Any], config: str, idx: int, row: list[Any]
    ) -> pn.Row:
        start_card = None
        reco_cards = []
        for idz, item_dto in enumerate(row):
            card = self.controller.get_item_viewer(item_dto, self)
            if self.controller.get_display_mode() == constants.DISPLAY_MODE_SINGLE:
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
        cards_row = pn.Row(start_card, *reco_cards[: self.page_size])
        row_with_navigation_buttons = self.create_navigation_elements_for_cards_row(
            cards_row, start_card, reco_cards
        )
        return pn.Row(pn.Column(cards_row, row_with_navigation_buttons))

    def create_navigation_elements_for_cards_row(
        self, cards_row: pn.Row, start_card: pn.layout.card.Card, reco_cards: list
    ) -> pn.Row:
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
        if widgets["page_size"] < len(widgets["reco_cards"]):
            widgets["page_size"] += self.page_size
            widgets["cards_row"].objects = [
                widgets["start_card"],
                *widgets["reco_cards"][
                    widgets["page_size"] - self.page_size : widgets["page_size"]
                ],
            ]
        widgets["prev_button"].disabled = False
        widgets["next_button"].disabled = (widgets["page_size"] + self.page_size) > len(
            widgets["reco_cards"]
        )

    def _update_prev(self, event, widgets: dict[any]):
        """
        :param event: Event that triggers the update
        :param widgets: Dictionary containing widgets to be updated
        :return: None

        This method updates the previous page of cards based on the current page size. If the page size is greater than the stored
        page size, it adjusts the page size and updates the cards to display the previous set of cards. Finally, it toggles the
        'next_button' and 'prev_button' widgets based on the new page size.
        """
        if widgets["page_size"] > self.page_size:
            widgets["page_size"] -= self.page_size
            widgets["cards_row"].objects = [
                widgets["start_card"],
                *widgets["reco_cards"][
                    widgets["page_size"] - self.page_size : widgets["page_size"]
                ],
            ]
        widgets["next_button"].disabled = False
        widgets["prev_button"].disabled = widgets["page_size"] <= self.page_size

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

        sidebar = self.config_based_nav_controls

        sidebar = self.get_version_information_and_append_to_sidebar(sidebar)

        # finally add onload, check if url parameter are defined in config and link to widgets
        pn.state.onload(self.update_widgets_from_url_parameter)

        self.template = pn.template.BootstrapTemplate(
            site_url="./",
            title=title,
            logo=logo,
            sidebar=[sidebar],
            main=[self.floating_elements, self.pagination_top, self.main_content, self.pagination],
            header_background=header_background,
        )

        return self.template
