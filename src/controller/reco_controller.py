import collections
import copy
import datetime
import importlib
import logging
import math
import re

import constants
from dto.item import ItemDto
from dto.user_item import UserItemDto
from envyaml import EnvYAML
from exceptions.date_validation_error import DateValidationError
from exceptions.empty_search_error import EmptySearchError
from exceptions.model_validation_error import ModelValidationError
from exceptions.user_not_found_error import UnknownUserError
from exceptions.item_not_found_error import UnknownItemError
from exceptions.empty_search_error import EmptySearchError
from util.postprocessing import FilterPostproc
from util.dto_utils import (
    update_from_props,
    dto_from_classname,
    dto_from_model,
    get_primary_idents,
)
from dto.user_item import UserItemDto
from dto.item import ItemDto
from dto.content_item import ContentItemDto
from envyaml import EnvYAML

logger = logging.getLogger(__name__)


class RecommendationController:
    FILTER_FIELD_MATRIX = {
        "genre": "genreCategory",
        "subgenre": "subgenreCategories",
        "theme": "thematicCategories",
        "show": "showId",
    }

    FILTER_LOGIC_MATRIX = {
        "same": "must",
        "different": "must_not",
        "choose": "must",
        "mixed": "",
    }

    def __init__(self, config):
        self.config = config
        self.item_accessor = BaseDataAccessorOpenSearch(config)
        if constants.MODEL_CONFIG_U2C in config:
            self.user_cluster_accessor = ClusteringModelClient(config)
        else:
            self.user_cluster_accessor = None
        self.reco_accessor = None
        self.postproc = FilterPostproc()
        self.components = collections.defaultdict(dict)
        self.watchers = collections.defaultdict(dict)
        self.callbacks = collections.defaultdict(dict)
        self.page_number = 1
        #
        # TODO - refactor this into model code
        #
        self.num_NN = 5  # num start items to fetch from backend per call
        self.num_items = 0  # num start items to fetch from backend per call
        self.num_items_single_view = 4
        self.num_items_multi_view = 4
        self.num_pages = 1
        self.display_mode = ""
        self.model_type = ""
        self.model_config = ""
        self.user_cluster = []  # refactor once clustering endpoint is better
        self.config_MDP2 = EnvYAML("./config/mdp2_lookup.yaml")

    def register(self, component_group, component, watcher=None, callback=None):
        self.components[component_group][component.params["label"]] = component
        if watcher:
            self.watchers[component_group][component.params["label"]] = watcher
        if callback:
            self.callbacks[component_group][component.params["label"]] = callback

    def get_item_defaults(self, component_name):
        return self.item_accessor.get_unique_vals_for_column(
            column=component_name, sort=True
        )

    def get_user_cluster(self):
        # TODO: improve the model config pass
        self.user_cluster_accessor.set_model_config(
            self.config[constants.MODEL_CONFIG_U2C]["clustering_models"][
                "U2C-Knn-Model"
            ]
        )
        self.user_cluster = self.user_cluster_accessor.get_user_cluster()
        return list(self.user_cluster.keys())

    def reset_page_number(self):
        self.page_number = 1

    def increase_page_number(self):
        self.page_number = self.get_page_number() + 1

    def decrease_page_number(self):
        self.page_number = self.get_page_number() - 1

    def get_page_number(self):
        return self.page_number

    def get_num_items(self):
        return self.num_items

    def set_num_items(self, num):
        self.num_items = num

    def get_num_pages(self):
        return self.num_pages

    def set_num_pages(self, item_hits):
        self.num_pages = math.ceil(item_hits / self.get_num_items())  # always round up

    def set_mode(self):
        # set model type: u2c or c2c
        self.model_config = [
            item for item in self.components["model_choice"].items() if item[1].value
        ][0][0]
        chosen_model = self.components["model_choice"][self.model_config].value[0]
        # ToDo: Needs refactoring. Gets value 'c2c_config' from configuration file based on position, should be based on key
        self.model_type = [
            model_type
            for model_type in self.config[self.model_config]
            for model in self.config[self.model_config][model_type]
            if model == chosen_model
        ][0]

        ## set display type, single or multi
        if len(self.components["model_choice"][self.model_config].value) > 1:
            self.display_mode = constants.DISPLAY_MODE_MULTI
            self.set_num_items(self.num_items_multi_view)
        else:
            self.display_mode = constants.DISPLAY_MODE_SINGLE
            self.set_num_items(self.num_items_single_view)

    def get_display_mode(self):
        return self.display_mode

    def get_model_type(self):
        return self.model_type

    #
    # TODO - refactor this into a factory class or similar
    #
    def get_item_viewer(self, item_dto: ItemDto):
        matches = re.search("^(.*)@(.*)$", item_dto.viewer)
        viewer_name, viewer_dir = matches.group(1), matches.group(2)
        module = importlib.import_module(viewer_dir)
        class_ = getattr(module, viewer_name)
        return class_(self.config)

    def set_model_and_strategy(self, model_info):
        """Sets an active model and a strategy in the controller for search

        Sets self.reco_accessor based on handler from config and self.reco_accessor endpoint from config

        :param model_info: model config from config yaml (should contain handler and model info)
        :return: Boolean True if successful
        """
        matches = re.search("^(.*)@(.*)$", model_info["handler"])
        handler_name, handler_dir = matches.group(1), matches.group(2)
        module = importlib.import_module(handler_dir)
        class_ = getattr(module, handler_name)
        self.reco_accessor = class_(self.config)
        self.reco_accessor.set_model_config(model_info)
        return True

    def get_model_params(self):
        return self.reco_accessor.get_model_params()

    def get_items_by_field(self, item_dto: ItemDto, ids: list):
        ids_prim = []
        ident, db_ident = get_primary_idents(self.config)
        try:
            for _id in ids:
                ids_prim.append(
                    self.item_accessor.get_primary_key_by_field(_id, db_ident)
                )
            item_dtos, num_items = self.item_accessor.get_items_by_ids(
                item_dto, ids_prim
            )
            return item_dtos
        except EmptySearchError as e:
            logger.warning("couldn't find item from user history")

    def get_items(self) -> tuple[list, list[list], str]:
        """Gets Items from OSS based on selected models, inputs and filters

        First gets selected models and display mode. Frontend can show items for a single
        model but also for multiple models at the same time
        :return:
        """
        self.set_mode()
        selected_models = self.components["model_choice"][self.model_config].value

        if not selected_models:
            raise ModelValidationError("Start by selecting one or more models!", {})

        if self.get_display_mode() == constants.DISPLAY_MODE_SINGLE:
            model_info = self.config[self.model_config][self.model_type][
                selected_models[0]
            ]
            self.set_model_and_strategy(model_info)
            return self.get_items_by_strategy_and_model(model_info)
        else:
            res = []
            for model in selected_models:
                model_info = self.config[self.model_config][self.model_type][model]
                self.set_model_and_strategy(model_info)
                hits, items, model_config = self.get_items_by_strategy_and_model(
                    model_info
                )
                res.append(items[0])
            return list(selected_models), res, self.model_config

    def get_items_by_strategy_and_model(
        self, model_info: dict
    ) -> tuple[list, list[list], str]:
        """Gets all items from OSS by model info

        Gets the start items by model info. The start item is the reference item a user searches.
        Each start item creates a new row in the frontend.

        :param model_info: Config of model in configuration yaml
        :return:
        """
        all_items = []
        item_hits, start_items = self._get_start_items(model_info)

        self.set_num_pages(item_hits)

        for index, start_item in enumerate(start_items):
            item_row = []
            item_row.append(start_item)
            try:
                nn_items, nn_dists = self._get_reco_items(start_item, model_info)

                # Find all filters
                all_chosen_filters = self._get_current_filter_state("reco_filter")
                if len(all_chosen_filters["remove_duplicate"]) > 0:
                    chosen_param = []
                    for item in all_chosen_filters["remove_duplicate"]:
                        chosen_param.append(item[1])
                    filtered_nn_items = self.postproc.filterDuplicates(
                        start_item, nn_items, chosen_param
                    )
                    nn_items = filtered_nn_items

                for idx, reco_item in enumerate(nn_items):
                    reco_item.dist = nn_dists[idx]
                    reco_item.position = constants.ITEM_POSITION_RECO
                    item_row.append(reco_item)

                all_items.append(item_row)
            except (UnknownUserError, UnknownItemError) as e:
                not_found_item = dto_from_classname(
                    class_name="NotFoundDto",
                    position=constants.ITEM_POSITION_START,
                    item_type=constants.ITEM_TYPE_CONTENT,
                    provenance=constants.ITEM_PROVENANCE_C2C,
                )
                item_row.append(not_found_item)
                all_items.append(item_row)
                continue
        return [model_info["display_name"]], all_items, self.model_config

    def _get_start_items_c2c(self, model: dict) -> tuple[int, list[ItemDto]]:
        """Gets search results based on selected model and active components

        First, gets the active components from registered components and checks these components
        with validator. Gets the accessor method from the components params and values from these
        components. The values are appended with an item dto and optional paging flag and filters.
        These final accessor values are passed to the accessor method in BaseDataAccessorOpenSearch.
        This function returns the actual item search results.

        :param model: Config of a model from the configuration yaml
        :return:
        """
        active_components = self._get_active_start_components()
        self._validate_input_data(active_components)
        accessor_method = self._get_data_accessor_method(active_components)
        accessor_values = [x.value for x in active_components]
        item_dto = dto_from_model(
            model=model,
            position=constants.ITEM_POSITION_START,
            item_type=constants.ITEM_TYPE_CONTENT,
            provenance=constants.ITEM_PROVENANCE_C2C,
        )
        accessor_values.insert(0, item_dto)
        accessor_values.append(self._get_current_filter_state("item_filter"))
        has_paging = [x.params.get("has_paging", False) for x in active_components]
        if any(has_paging):
            accessor_values.extend(
                [(self.get_page_number() * self.get_num_items()), self.get_num_items()]
            )
        logger.info(
            "calling " + accessor_method + " with values " + str(accessor_values)
        )
        function_pointer = getattr(self.item_accessor, accessor_method)
        search_result, total_hits = function_pointer(*accessor_values)
        return total_hits, search_result

    ## - refactor once we have proper user clustering/sampling
    def _get_start_users_u2c(self, model: dict) -> tuple[int, list]:
        active_components = self._get_active_start_components()
        has_paging = [x.params.get("has_paging", False) for x in active_components]
        self._validate_input_data(active_components)
        start_idx, end_idx = (0, 0)
        if any(has_paging):
            start_idx = (self.get_page_number() - 1) * self.get_num_items()
            end_idx = start_idx + self.get_num_items()
        # create the user dto from model info
        user_dto = dto_from_model(
            model=model,
            position=constants.ITEM_POSITION_START,
            item_type=constants.ITEM_TYPE_USER,
            provenance=constants.ITEM_PROVENANCE_U2C,
        )
        # only one active user component at this time
        if len(active_components) > 1:
            raise Exception(
                "Can't use more than one selection widget for user selection"
            )
        if active_components[0].params["label"] == "cluster_users":
            return self._get_start_users_by_cluster(
                user_dto, active_components[0], start_idx, end_idx
            )
        elif active_components[0].params["label"] == "genre_users":
            return self._get_start_users_by_genre(
                user_dto, active_components[0], start_idx, end_idx
            )
        else:
            raise Exception(
                "Unknown user selection widget ["
                + active_components[0].params.label
                + "]"
            )

    def _get_start_users_by_genre(
        self, user_dto: UserItemDto, genre_widget, start_idx, end_idx
    ) -> tuple[int, list[UserItemDto]]:
        # TODO: improve the model config pass
        self.user_cluster_accessor.set_model_config(
            self.config[constants.MODEL_CONFIG_U2C]["clustering_models"][
                "U2C-Knn-Model"
            ]
        )
        field_map = self.config[constants.MODEL_CONFIG_U2C]["clustering_models"][
            "U2C-Knn-Model"
        ]["field_mapping"]
        response = self.user_cluster_accessor.get_users_by_category(genre_widget.value)
        num_users = len(response[genre_widget.value])
        users = []
        for user_props in response[genre_widget.value][start_idx:end_idx]:
            new_user = copy.copy(user_dto)
            new_user.source = "Primäres Genre"
            new_user.source_value = genre_widget.value
            new_user = update_from_props(new_user, user_props, field_map)
            users.append(new_user)
        return num_users, users

    def _get_start_users_by_cluster(
        self, user_dto: UserItemDto, cluster_widget, start_idx, end_idx
    ) -> tuple[int, list[UserItemDto]]:
        cluster_name = cluster_widget.value
        user_ids = self.user_cluster[cluster_name][start_idx:end_idx]
        users = []
        for user_id in user_ids:
            new_user = copy.copy(user_dto)
            new_user.source = "Cluster-Nutzer"
            new_user.source_value = cluster_name
            new_user.id = user_id
            users.append(new_user)
        return len(self.user_cluster[cluster_name]), users

    def _get_start_items(self, model: dict) -> tuple[int, list[ItemDto]]:
        """Decides if C2C or U2C are used for the search query for the start items

        :param model: Config of models from the configuration yaml
        :return:
        """
        if self.model_type == constants.MODEL_TYPE_C2C:
            return self._get_start_items_c2c(model)
        else:
            return self._get_start_users_u2c(model)

    def _get_reco_items(self, start_item, model):
        """Decides if C2C or U2C are used for the search query for the reco items

        :param start_item: The start item (reference item) for which reco items are searched
        :param model: Config of models from the configuration yaml
        :return:
        """
        if self.model_type == constants.MODEL_TYPE_C2C:
            return self._get_reco_items_c2c(start_item, model)
        else:
            return self._get_reco_items_u2c(start_item, model)

    def _get_reco_items_c2c(self, start_item: ItemDto, model: dict):
        """Gets recommended items based on the start item and filters

        :param start_item: The start item (reference item) for which reco items are searched
        :param model: Config of models from the configuration yaml
        :return:
        """
        reco_filter = self._get_current_filter_state("reco_filter")
        transposed_filter = self._transpose_reco_filter_state(reco_filter, start_item)
        kidxs, nn_dists, field = self.reco_accessor.get_k_NN(
            start_item, (self.num_NN + 1), transposed_filter
        )
        kidxs, nn_dists = self._align_kidxs_nn(start_item.id, kidxs, nn_dists)
        item_dto = dto_from_model(
            model=model,
            position=constants.ITEM_POSITION_RECO,
            item_type=constants.ITEM_TYPE_CONTENT,
            provenance=constants.ITEM_PROVENANCE_C2C,
        )
        return (
            self.item_accessor.get_items_by_ids(
                item_dto, kidxs[: self.num_NN], constants.MODEL_TYPE_C2C
            )[0],
            nn_dists[: self.num_NN],
        )

    def _get_reco_items_u2c(self, start_item: ItemDto, model: dict):
        kidxs, nn_dists, field = self.reco_accessor.get_recos_user(
            start_item, (self.num_NN + 1)
        )
        ident, db_ident = get_primary_idents(self.config)
        kidxs_prim = []
        try:
            for kidx in kidxs:
                kidxs_prim.append(
                    self.item_accessor.get_primary_key_by_field(kidx, db_ident)
                )
        except EmptySearchError as e:
            logger.warning(str(e))

        reco_item = dto_from_model(
            model=model,
            position=constants.ITEM_POSITION_RECO,
            item_type=constants.ITEM_TYPE_CONTENT,
            provenance=constants.ITEM_PROVENANCE_U2C,
        )
        return self.item_accessor.get_items_by_ids(
            reco_item, kidxs_prim[: self.num_NN], constants.MODEL_TYPE_U2C
        )[0], nn_dists[: self.num_NN]

    def _align_kidxs_nn(self, content_id, kidxs, nn_dists):
        try:
            idx = kidxs.index(content_id)
            kidxs.pop(idx)
            nn_dists.pop(idx)
            return kidxs, nn_dists
        except ValueError:
            return kidxs, nn_dists

    def _get_data_accessor_method(self, active_components):
        """Gets a accessor method from the active components.

        Every component should contain a accessor_method in params but
        for an active component there should be no different accessor methods

        :param active_components:
        :return:
        """
        accessor_method = set([])
        for component in active_components:
            accessor_method.add(component.params["accessor"])
        if len(accessor_method) > 1:
            logger.warning(
                "Can't have different accessors for same active component group"
            )
        return list(accessor_method)[0]

    def _validate_input_data(self, active_components):
        """Gets validator based on given active components

        Validator must be in component params, otherwise a Key Error gets raised.
        Validator is a string which must be defined as a callable function in this controller.

        :param active_components: List of active components
        :return:
        """
        for component in active_components:
            if component.params.get("validator", False):
                validator = getattr(self, component.params["validator"])
                if callable(validator):
                    logger.info(
                        "calling "
                        + component.params["validator"]
                        + " on component "
                        + component.name
                    )
                    validator(component)
                else:
                    raise AttributeError(
                        "Input item ["
                        + component.name
                        + "] must provide a validation callback"
                    )
            else:
                raise KeyError(
                    "Input item [" + component.name + "] must provide a validation key"
                )

    def _check_user(self, user_field):
        if not isinstance(user_field.value, str):
            raise ValueError("User cluster must be identified as a string")

    def _check_date(self, date_field):
        if not isinstance(date_field.value, datetime.date):
            raise DateValidationError("DatePickers must provide a date", {})

    def _check_crid(self, crid_field):
        if not isinstance(crid_field.value.strip(), str):
            raise ValueError("Crid must be a string")
        elif not crid_field.value.strip().startswith("crid://"):
            raise ValueError("Id must be of format crid://")

    def _check_urn(self, urn_field):
        if not isinstance(urn_field.value.strip(), str):
            raise ValueError("Crid must be a string")
        elif not urn_field.value.strip().startswith("urn:"):
            raise ValueError("Id must be of format urn:")

    def _check_url(self, url_field):
        # overwrite active_component from url to crid
        if not isinstance(url_field.value, str):
            raise ValueError("URL must be a string")
        elif not url_field.value.startswith("https://"):
            raise ValueError("URL must be of format https://")

    def _check_text(self, text_field):
        if not isinstance(text_field.value, str):
            raise ValueError("Text must be a string")

    def _check_text(self, text_field):
        if not isinstance(text_field.value, str):
            raise ValueError("Text must be a string")

    def _check_category(self, genre_field):
        if genre_field.value not in self.get_item_defaults("genreCategory"):
            raise ValueError("Unknown category [" + genre_field.value + "]")

    #
    def _get_active_start_components(self) -> list:
        """Gets a list of active components

        For C2C models 'item_choice' components which are visible are active components.
        For U2C models 'user_choice' components which are active are active components.
        Components should be registered in controller before

        :return: list of active start components
        """
        if self.model_type == constants.MODEL_TYPE_U2C:
            return list(
                filter(
                    lambda x: x.params["active"],
                    self.components["user_choice"].values(),
                )
            )
        elif self.model_type == constants.MODEL_TYPE_C2C:
            return list(
                filter(lambda x: x.visible, self.components["item_choice"].values())
            )
        else:
            raise TypeError("Unknown model type [" + self.model_type + "]")

    def _get_current_filter_state(self, filter_group):
        filter_state = collections.defaultdict(dict)
        for component in self.components[filter_group].values():
            filter_state[component.params["label"]] = component.value
        return filter_state

    def _transpose_reco_filter_state(self, reco_filter, start_item):
        transposed = collections.defaultdict(dict)
        bool_terms = collections.defaultdict(list)
        script_term = collections.defaultdict(dict)

        for filter_element in reco_filter.items():
            label, value = filter_element
            if not value:
                continue

            if isinstance(value, list):
                value = value[0]

            action, actor = label.split("_")

            if action == "termfilter":
                bool_terms = self._prepare_query_term_condition_statement(
                    value, start_item, reco_filter, bool_terms
                )
            elif action == "rangefilter":
                bool_terms = self._prepare_query_range_condition_statement(
                    value, bool_terms
                )
            elif action == "sort":
                transposed["sort"] = value
            elif action == "clean":
                script_term = self._prepare_query_bool_script_statement(value)
            else:
                logger.warning(
                    "Received unknown filter action [" + action + "]. Omitting."
                )

        if bool_terms:
            transposed["bool"] = bool_terms
        if script_term:
            transposed["bool"]["filter"] = script_term

        return transposed

    def _prepare_query_range_condition_statement(self, value, bool_terms):
        bool_terms["must"].append({"range": value})

        return bool_terms

    def _prepare_query_term_condition_statement(
        self, value: list, start_item: ItemDto, reco_filter: dict, bool_terms: dict
    ) -> dict:
        transposed_values = []

        logic, field = value.split("_")
        operator = self.FILTER_LOGIC_MATRIX[logic]  ## contains "must"
        if logic != "choose":
            if isinstance(
                start_item.__getattribute__(self.FILTER_FIELD_MATRIX[field]), list
            ):
                transposed_values.extend(
                    start_item.__getattribute__(self.FILTER_FIELD_MATRIX[field])
                )
            else:
                transposed_values.append(
                    start_item.__getattribute__(self.FILTER_FIELD_MATRIX[field])
                )
        else:  ## we're in "choose_genre", or "choose_subgenre" etc..
            if field == "erzählweise":
                reco_filter["value_genreCategory"] = (
                    self.get_genres_and_subgenres_from_upper_category(
                        reco_filter["value_erzaehlweiseCategory"], "genres"
                    )
                )
                field = "genre"
            elif field == "inhalt":
                reco_filter["value_subgenreCategories"] = (
                    self.get_genres_and_subgenres_from_upper_category(
                        reco_filter["value_inhaltCategory"], "subgenres"
                    )
                )
                field = "subgenre"
            filter_key = "value_" + self.FILTER_FIELD_MATRIX[field]
            transposed_values.extend(reco_filter[filter_key])
        term = collections.defaultdict(dict)

        if len(transposed_values):
            term["terms"][self.FILTER_FIELD_MATRIX[field] + ".keyword"] = (
                transposed_values
            )

        if term:
            bool_terms[operator].append(term)

        return bool_terms

    def _prepare_query_bool_script_statement(self, values):
        filter_statement = collections.defaultdict(dict)
        filter_statement["script"] = collections.defaultdict(dict)
        expr_template = "doc['###.keyword'].length > 0"
        expr = ""

        for idx, one_element in enumerate(values):
            expr = expr + expr_template.replace("###", values)
            if (idx + 1) < len(values):
                expr = expr + " && "

        filter_statement["script"]["script"]["source"] = expr
        return filter_statement

    def _get_model_type_by_model_key(self, model_key):
        for ctype in [constants.MODEL_CONFIG_C2C, constants.MODEL_CONFIG_U2C]:
            for mtype in [constants.MODEL_TYPE_C2C, constants.MODEL_TYPE_U2C]:
                for model in self.config[ctype][mtype].keys():
                    if model == model_key:
                        return mtype
        raise ValueError("Unknown model type of model key [" + model_key + "]")

    def reset_defaults(self, widget_groups):
        for widget_group in widget_groups:
            for label, component in self.components[widget_group].items():
                if self.watchers[widget_group].get(label):
                    component.param.unwatch(self.watchers[widget_group][label])
                component.value = component.params["reset_to"]
            for label, component in self.components[widget_group].items():
                if self.callbacks[widget_group].get(label):
                    component.param.watch(self.callbacks[widget_group][label], "value")

    def reset_component(self, component_group, component_label, to_value="default"):
        component = self.components[component_group][component_label]
        if self.watchers[component_group].get(component_label):
            component.param.unwatch(self.watchers[component_group][component_label])
            if to_value == "default":
                component.value = component.params["reset_to"]
            else:
                component.value = to_value
            component.param.watch(
                self.callbacks[component_group][component_label], "value"
            )

    def import_filter_rules(self):
        1

    def export_filter_rules(self):
        1

    def get_genres_and_subgenres_from_upper_category(
        self, selected_upper_categories, category
    ):  # category = 'genres' or 'subgenres'
        all_selected = []
        for items in selected_upper_categories:
            all_selected.extend(self.config_MDP2["categories_MDP2"][items][category])
        return all_selected

    def get_upper_genres_and_subgenres(self, selected):
        if isinstance(selected, list):
            all_categories = []
            for category in self.config_MDP2["categories_MDP2"]:
                for item in selected:
                    if item in self.config_MDP2["categories_MDP2"][category]["genres"]:
                        all_categories.append(
                            self.config_MDP2["categories_MDP2"][category]["Erzählweise"]
                        )
                    elif (
                        item
                        in self.config_MDP2["categories_MDP2"][category]["subgenres"]
                    ):
                        all_categories.append(
                            self.config_MDP2["categories_MDP2"][category]["Inhalt"]
                        )
            return ", ".join(set(all_categories))
        else:
            for category in self.config_MDP2["categories_MDP2"]:
                if selected in self.config_MDP2["categories_MDP2"][category]["genres"]:
                    return self.config_MDP2["categories_MDP2"][category]["Erzählweise"]
                elif (
                    selected
                    in self.config_MDP2["categories_MDP2"][category]["subgenres"]
                ):
                    return self.config_MDP2["categories_MDP2"][category]["Inhalt"]
                else:
                    pass
            return ""
