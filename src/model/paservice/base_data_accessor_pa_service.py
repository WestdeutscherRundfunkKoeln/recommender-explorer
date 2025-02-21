import copy
import logging
import pprint
from typing import Any

import httpx
from dto.item import ItemDto
from exceptions.config_error import ConfigError
from exceptions.empty_search_error import EmptySearchError
from exceptions.endpoint_error import EndpointError
from model.base_data_accessor import BaseDataAccessor
from util.dto_utils import update_from_props

#loggin preference
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
formatter = logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


WEIGHTS = (
    "weight_audio",
    "weight_video",
    "weight_beitrag",
    "weight_fotostrecke",
    "weight_link",
)


class BaseDataAccessorPaService(BaseDataAccessor):
    def __init__(self, config):
        self.not_implemented_error_message = "This method is not implemented yet"
        self.pa_service_config = config.get("pa_service")
        if self.pa_service_config:
            self.host = self.pa_service_config.get("host")
            self.auth_header = self.pa_service_config.get("auth_header")
            self.auth_header_value = self.pa_service_config.get("auth_header_value")
            self.http_proxy = self.pa_service_config.get("http_proxy")
            self.https_proxy = self.pa_service_config.get("https_proxy")
            self.endpoint = self.pa_service_config.get("endpoint")
            self.field_mapping = self.pa_service_config.get("field_mapping")
            self.number_of_recommendations = self.pa_service_config.get(
                "number_of_recommendations", 10
            )

        if not self.pa_service_config:
            raise ConfigError(
                "Could not get valid Configuration for Service from config yaml. BaseDataAccessorPaService needs correctly configured Service, "
                "expect Configuration in Key: pa_service",
                {},
            )
        elif not self.host:
            raise ConfigError(
                "Could not get valid Configuration for Service from config yaml. BaseDataAccessorPaService needs correctly configured Service, "
                "expect Configuration in Key: pa_service.host",
                {},
            )
        elif not self.endpoint:
            raise ConfigError(
                "Could not get valid Configuration for Service from config yaml. BaseDataAccessorPaService needs correctly configured Service, "
                "expect Configuration in Key: pa_service.endpoint",
                {},
            )
        elif not self.field_mapping:
            raise ConfigError(
                "Could not get valid Configuration for Service from config yaml. BaseDataAccessorPaService needs correctly configured Service, "
                "expect Configuration in Key: pa_service.field_mapping",
                {},
            )
        elif not self.auth_header:
            raise ConfigError(
                "Could not get valid Configuration for Service from config yaml. BaseDataAccessorPaService needs correctly configured Service, "
                "expect Configuration in Key: pa_service.auth_header",
                {},
            )
        elif not self.auth_header_value:
            raise ConfigError(
                "Could not get valid Configuration for Service from config yaml. BaseDataAccessorPaService needs correctly configured Service, "
                "expect Configuration in Key: pa_service.auth_header_value",
                {},
            )
        elif not isinstance(self.number_of_recommendations, int):
            raise ConfigError(
                "Could not get valid Configuration for Service from config yaml. BaseDataAccessorPaService needs correctly configured Service, "
                "expect int value in Configuration in Key: pa_service.number_of_recommendations",
                {},
            )

        headers = (
            {
                "Content-Type": "application/json",
                "accept": "*/*",
                self.auth_header: self.auth_header_value,
            }
            if self.auth_header and self.auth_header_value
            else None
        )
        proxies = (
            {"http://": self.http_proxy, "https://": self.https_proxy}
            if self.http_proxy and self.https_proxy
            else None
        )
        self.client = httpx.Client(proxies=proxies, headers=headers, base_url=self.host)

    def get_items_by_ids(self, ids):
        raise NotImplementedError(self.not_implemented_error_message)

    def get_item_by_crid(self, crid):
        raise NotImplementedError(self.not_implemented_error_message)

    def get_items_by_date(self, start_date, end_date, offset=0, size=-1):
        raise NotImplementedError(self.not_implemented_error_message)

    def get_items_date_range_limits(self):
        raise NotImplementedError(self.not_implemented_error_message)

    def get_top_k_vals_for_column(self, column, k):
        raise NotImplementedError(self.not_implemented_error_message)

    def get_unique_vals_for_column(self, column, sort=True):
        raise NotImplementedError(self.not_implemented_error_message)

    def get_item_by_external_id(self, item: ItemDto, external_id, filter={}):
        """
        Gets the response from the configured PA Service Endpoint by sending just the external Id.
        Most Configurations come from Service Config in File and the endpoint from the model itself.
        When request returns results, these will be parsed into the given Item DTO and these will be returned.

        :param item: The item dto class where the result should be stored
        :param external_id: The external ID to search for the start item and its recommendations
        :param filter: not used for now
        :return: Start Item and Recommendations in the given Item DTO
        """
        # Distinguish which endpoint to triger
        if filter['empfehlungstyp'] == 'Ähnlichkeit' or filter['empfehlungstyp'] is None :
            self.endpoint = 'v1/br/similar-content'
        elif filter['empfehlungstyp'] == 'Diversität':
            self.endpoint = 'v1/br/diverse-content'
        elif filter['empfehlungstyp'] == 'Aktualität':
            self.endpoint = 'v1/br/recent-content'

        json = build_request(external_id, filter)
        pprint.pprint(json)

        try:
            response = self.client.post(
                self.endpoint, json=build_request(external_id, filter)
            )
            response.raise_for_status()
            pprint.pprint(response   )
            return self.__get_items_from_response(item, response.json())
        except httpx.HTTPStatusError as e:
            logging.error(e, exc_info=True)
            raise EndpointError(
                f"Couldn't get a valid response from endpoint [{self.host}/{self.endpoint}]: {e.response.read().decode()}",
                {"exc": str(e)},
            )
        except Exception as e:
            logging.error(e, exc_info=True)
            raise EndpointError(
                f"Couldn't get a valid response from endpoint [{self.host}/{self.endpoint}]: {str(e)}",
                {"exc": str(e)},
            )

    def __get_items_from_response(
        self, item_dto: ItemDto, response: dict[str, Any]
    ) -> tuple[list, int]:
        """
        Gets the resulting items from the pa service response in json
        Gets total items count from search response and iterates over result items and map
        these results to the given Item DTO

        :param item_dto: The item dto class where the result should be stored
        :param response: Response from pa service in json format
        :param provenance:
        :return: List of item dtos, total items count
        """
        items = response["items"]
        total_items = len(items)

        if total_items < 1 or not len(items):
            raise EmptySearchError("Keine Treffer gefunden", {})
        item_dtos = []
        for index, pa_service_hit in enumerate(items):
            new_item_dto = copy.copy(item_dto)
            item_hit = pa_service_hit["item"]
            new_item_dto = update_from_props(new_item_dto, item_hit, self.field_mapping)
            new_item_dto.dist = pa_service_hit.get("score", 0)
            new_item_dto._position = "start" if index == 0 else "reco"
            item_dtos.append(new_item_dto)

        return item_dtos[: self.number_of_recommendations + 1], total_items


def build_request(external_id: str, filter: dict[str, Any]) -> dict[str, Any]:
    request_body: dict[str, Any] = {"referenceId": external_id, "reco": "true"}
    if "relativerangefilter_duration" in filter:
        request_body["maxDurationFactor"] = filter["relativerangefilter_duration"]
    if "blacklist_externalid" in filter:
        request_body["excludedIds"] = (
            filter["blacklist_externalid"].replace(" ", "").split(",")
        )

    if "empfehlungstyp" in filter:
        request_body["empfehlungstyp"] = filter["empfehlungstyp"]

    if "empfehlungstyp_direction" in filter:
        request_body["empfehlungstyp_direction"] = filter["empfehlungstyp_direction"]

    if "previous_external_ids" in filter:
        request_body["previous_external_ids"] = filter["previous_external_ids"]

    return request_body
