import json
import logging
from typing import Any, Callable
from dto.item import ItemDto
from dto.user_item import UserItemDto
from exceptions.item_not_found_error import UnknownItemError
from exceptions.user_not_found_error import UnknownUserError
from model.nn_seeker import NnSeeker
from util.dto_utils import get_primary_idents
from model.rest.nn_seeker_paservice_request_helper import RequestHelper

logger = logging.getLogger(__name__)

RequestParamsBuilder = Callable[[ItemDto, str], dict[str, Any]]

class NnSeekerRest(NnSeeker, RequestHelper):
    def __init__(self, config, max_num_neighbours=16):
        RequestHelper.__init__(self)
        self.__config = config
        self.__max_num_neighbours = max_num_neighbours

    def get_k_NN(
        self, item: ItemDto, k: int, nn_filter: dict[str, Any] | None
    ) -> tuple[list[str], list[float], Any, dict[Any, Any]]:
        return self._get_recos(
            self._get_request_params_c2c_s2c, UnknownItemError, item, k, nn_filter
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
        status, data_str = self.post(json_body=params)
        pa_recos = json.loads(data_str)

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

        result = nn_filter.copy()

        editorial = result.pop("editorialCategories", None)
        if editorial:
            result["includedCategories"] = ",".join(editorial)

        return result

    def set_model_config(self, model_config):
        RequestHelper.set_model_config(self, model_config, endpoint_key="endpoint")


    @staticmethod
    def _parse_response(response: dict[str, Any]) -> tuple[list[str], list[float], dict[Any, Any]]:
        raise NotImplementedError()

    def _get_request_params_c2c_s2c(self, item: ItemDto, oss_field: str) -> dict[str, Any]:
        raise NotImplementedError()

    def _get_request_params_u2c(self, item: ItemDto, oss_field: str) -> dict[str, Any]:
        raise NotImplementedError()