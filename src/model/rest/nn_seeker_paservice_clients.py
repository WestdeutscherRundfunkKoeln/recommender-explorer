import logging
from model.rest.nn_seeker_paservice_request_helper import RequestHelper
from typing import Dict

logger = logging.getLogger(__name__)

class NnSeekerPaServiceClients(RequestHelper):
    def __init__(self, model_info: Dict, max_num_neighbours: int = 16):
        super().__init__()
        self.model_info = model_info
        self.__max_num_neighbours = max_num_neighbours
        self.set_model_config(self.model_info, endpoint_key="clients_endpoint")

    def get_clients(self):
        status, data = self.get()
        if status != 200:
            raise ValueError(f"Failed to get clients with status {status}")
        identifiers = [client["identifier"] for client in data.get("clients", [])]
        return identifiers
