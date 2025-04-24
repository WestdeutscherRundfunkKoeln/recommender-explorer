import json
import logging
from typing import Any, Callable

from urllib3 import PoolManager, Retry

from dto.item import ItemDto
from dto.user_item import UserItemDto
from exceptions.item_not_found_error import UnknownItemError
from exceptions.user_not_found_error import UnknownUserError
from model.nn_seeker import NnSeeker
from util.dto_utils import get_primary_idents

logger = logging.getLogger(__name__)

RequestParamsBuilder = Callable[[ItemDto, str], dict[str, Any]]

class NnSeekerRest(NnSeeker):
    def __init__(self, config, max_num_neighbours=16):
        self.__max_num_neighbours = max_num_neighbours
        self.__retry_connection = 5
        self.__retry_reads = 2
        self.__retry_redirects = 5
        self.__backoff_factor = 0.1
        self._model_props = {}
        self._endpoint: str = ""
        self.__config = config

    def get_k_NN(
        self, item: ItemDto, k: int, nn_filter: dict[str, Any] | None
    ) -> tuple[list[str], list[float], Any, dict[Any, Any]]:
        return self._get_recos(
            self._get_request_params_c2c, UnknownItemError, item, k, nn_filter
        )

    def get_recos_user(
        self, user: UserItemDto, n_recos: int, nn_filter: dict[str, Any] | None = None
    ) -> tuple[list[str], list[float], Any, dict[Any, Any]]:
        return self._get_recos(
            self._get_request_params_u2c, UnknownUserError, user, n_recos, nn_filter
        )

    def get_max_num_neighbours(self, content_idx):
        return self.__max_num_neighbours

    def _get_recos(
        self,
        request_params_builder: RequestParamsBuilder,
        unknown_item_exception: type[UnknownItemError] | type[UnknownUserError],
        item: ItemDto,
        k: int,
        nn_filter: dict[str, Any] | None,
    ) -> tuple[list[str], list[float], Any, dict[Any, Any]]:
        _, oss_field = get_primary_idents(self.__config)

        params = self._build_request(request_params_builder, item, oss_field, nn_filter)
        status, pa_recos = self._post_2_endpoint(params)
        # TODO - add better status and error handling
        if status != 200:
            raise unknown_item_exception(
                self._endpoint,
                item.__getattribute__(oss_field),
                {},
            )

        result = self._parse_response(pa_recos)

        recomm_content_ids, nn_dists, utilities = result

        return recomm_content_ids, nn_dists, oss_field , utilities

    def _post_2_endpoint(self, post_params):
        retries = Retry(
            connect=self.__retry_connection,
            read=self.__retry_reads,
            redirect=self.__retry_redirects,
            backoff_factor=self.__backoff_factor,
        )
        http = PoolManager(retries=retries)

        logger.info(
            "calling [" + self._endpoint + "] with params " + json.dumps(post_params)
        )

        response = http.request(
            "POST", self._endpoint, json=post_params, headers=self._get_headers()
        )
        status_code = response.status
        data = json.loads(response.data.decode("utf-8"))

        logger.info("Got status code [" + str(status_code) + "] and data: ")
        logger.info(data)

        return status_code, data

    def _build_request(
        self,
        request_params_builder: Callable[[ItemDto, str], dict[str, Any]],
        item: ItemDto,
        oss_field: str,
        nn_filter: dict[str, Any] | None,
    ):
        return {
            **self._get_filters(nn_filter),
            **self._get_model_config_params(),
            **request_params_builder(item, oss_field),
        }

    def _get_model_config_params(self) -> dict[str, Any]:
        if not self._model_props:
            raise ValueError("Model properties not set")
        return {
            p.removeprefix("param_"): v
            for p, v in self._model_props.items()
            if p.startswith("param_")
        }

    def _get_headers(self):
        if not self._model_props:
            raise ValueError("Model properties not set")
        return {
            self._model_props["auth_header"]: self._model_props["auth_header_value"],
        }

    @staticmethod
    def _get_filters(nn_filter: dict[str, Any] | None) -> dict[str, Any]:
        if not nn_filter:
            return {}

        selected_params = {
            "includedCategories": ",".join(nn_filter["editorialCategories"])
            if nn_filter.get("editorialCategories")
            else None,
            "filter": nn_filter.get("filter"),
            "refinement": nn_filter.get("refinement"),
            "utilities": nn_filter.get("utilities"),
            "weights": nn_filter.get("weights"),
        }

        return {k: v for k, v in selected_params.items() if v is not None}

    def set_model_config(self, model_config):
        self._endpoint = model_config["endpoint"]
        self._model_props = model_config["properties"]


    @staticmethod
    def _parse_response(response: dict[str, Any]) -> tuple[list[str], list[float], dict[Any, Any]]:
        raise NotImplementedError()

    def _get_request_params_c2c(self, item: ItemDto, oss_field: str) -> dict[str, Any]:
        raise NotImplementedError()

    def _get_request_params_u2c(self, item: ItemDto, oss_field: str) -> dict[str, Any]:
        raise NotImplementedError()
