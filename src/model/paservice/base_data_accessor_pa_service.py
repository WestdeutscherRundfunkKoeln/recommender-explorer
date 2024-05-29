import copy
import json
import logging
import requests
import constants

from model.base_data_accessor import BaseDataAccessor
from exceptions.empty_search_error import EmptySearchError
from exceptions.endpoint_error import EndpointError
from dto.item import ItemDto
from util.dto_utils import update_from_props

logger = logging.getLogger(__name__)


class BaseDataAccessorPaService(BaseDataAccessor):
    def __init__(self, config):
        self.config = config
        self.pa_service_config = self.config.get('pa_service', None)
        if self.pa_service_config:
            self.host = self.pa_service_config.get('host', None)
            self.auth_header = self.pa_service_config.get('auth_header', None)
            self.auth_header_value = self.pa_service_config.get('auth_header_value', None)
            self.http_proxy = self.pa_service_config.get('http_proxy', None)
            self.https_proxy = self.pa_service_config.get('https_proxy', None)
            self.field_mapping = self.pa_service_config.get('field_mapping', None)

    def get_items_by_ids(self, ids):
        pass

    def get_item_by_crid(self, crid):
        pass

    def get_items_by_date(self, start_date, end_date, offset=0, size=-1):
        pass

    def get_items_date_range_limits(self):
        pass

    def get_top_k_vals_for_column(self, column, k):
        pass

    def get_unique_vals_for_column(self, column, sort=True):
        pass

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
        try:
            pa_service_model_config = self.config['c2c_config']['c2c_models']['PA-Service-Only']
            pa_service_endpoint = pa_service_model_config.get('endpoint', None)

            if self.host and pa_service_endpoint:
                url = self.host + '/' + pa_service_endpoint

                request_body = {
                    "referenceId": external_id,
                    "reco": "true"
                }

                headers = None
                if self.auth_header and self.auth_header_value:
                    headers = {
                        'Content-Type': 'application/json',
                        'accept': '*/*',
                        self.auth_header: self.auth_header_value
                    }

                proxies = None
                if self.http_proxy and self.https_proxy:
                    proxies = {
                        'http': self.http_proxy,
                        'https': self.https_proxy
                    }

                request_params = {
                    'url': url,
                    'json': request_body
                }

                if headers:
                    request_params['headers'] = headers

                if proxies:
                    request_params['proxies'] = proxies

                response = requests.post(**request_params)

                if response.status_code == 200:
                    # Print the response data
                    print(response.json())
                    return self.__get_items_from_response(item, response.json())
                else:
                    # If there was an error, print the status code and error message
                    logging.error("Request Error:", response.status_code, response.text)
                    raise EndpointError(
                        'Could not get result from Endpoint: ' + url + 'with request parameters: ' + json.dumps(request_params, indent=4) + '. Status Code: ' + response.status_code)
        except Exception as e:
            logging.error(e)
            raise EndpointError("Couldn't get a valid response from endpoint [" + self.host + '/' + pa_service_endpoint + ']', {})

    def __get_items_from_response(self, item_dto: ItemDto, response, provenance=constants.ITEM_PROVENANCE_C2C) -> tuple[list, int]:
        """
        Gets the resulting items from the pa service response in json
        Gets total items count from search response and iterates over result items and map
        these results to the given Item DTO

        :param item_dto: The item dto class where the result should be stored
        :param response: Response from pa service in json format
        :param provenance:
        :return: List of item dtos, total items count
        """
        items = response['items']
        total_items = len(items)

        if total_items < 1 or not len(items):
            raise EmptySearchError("Keine Treffer gefunden", {})
        item_dtos = []
        for index, pa_service_hit in enumerate(items):
            new_item_dto = copy.copy(item_dto)
            item_hit = pa_service_hit['item']
            new_item_dto = update_from_props(new_item_dto, item_hit, self.field_mapping)
            new_item_dto.__setattr__('score', pa_service_hit.get('score', 0))
            if index == 0:
                new_item_dto.__setattr__('_position', 'start')
            else:
                new_item_dto.__setattr__('_position', 'reco')
            item_dtos.append(new_item_dto)
        return item_dtos, total_items
