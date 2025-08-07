import json
import logging
from model.rest.nn_seeker_paservice_request_helper import RequestHelper

logger = logging.getLogger(__name__)

class NnSeekerPaServiceClients(RequestHelper):
    def __init__(self, config, model_info, max_num_neighbours=16):
        super().__init__()
        self.__config = config
        self.model_info = model_info
        self.__max_num_neighbours = max_num_neighbours

    def get_clients(self):
        self.set_model_config(self.model_info, endpoint_key="clients_endpoint")
        status, data_str = self.get()
        if status != 200:
            logger.error(f"Failed to get clients from {self._endpoint} with status {status}")
            return []
        data = json.loads(data_str)
        identifiers = [client["identifier"] for client in data.get("clients", [])]
        return identifiers
