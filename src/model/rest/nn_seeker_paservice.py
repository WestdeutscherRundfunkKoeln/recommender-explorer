from typing import Any

from dto.item import ItemDto
from model.rest.nn_seeker_rest import NnSeekerRest


class NnSeekerPaService(NnSeekerRest):
    def __init__(self, config):
        self.__max_num_neighbours = 16
        self.__configuration_c2c = "relatedItems"
        self.__configuration_u2c = "forYou"

        super().__init__(config)

    def _get_request_params_c2c(self, item: ItemDto, oss_field: str) -> dict[str, Any]:
        return {
            "configuration": self.__configuration_c2c,
            "assetId": item.__getattribute__(oss_field),
            "limit": self.__max_num_neighbours,
        }

    def _get_request_params_u2c(self, item: ItemDto, oss_field: str) -> dict[str, Any]:
        return {
            "configuration": self.__configuration_u2c,
            "explain": True,
            "userId": item.id,
        }

    @staticmethod
    def _parse_response(response: dict[str, Any]) -> tuple[list[str], list[float]]:
        recomm_content_ids = []
        nn_dists = []
        for reco in response["recommendations"]:
            nn_dists.append(reco["score"])
            recomm_content_ids.append(reco["asset"]["assetId"])
        return recomm_content_ids, nn_dists

    def get_max_num_neighbours(self, content_id):
        return self.__max_num_neighbours

    def get_model_params(self):
        model_params = {}
        model_params["Error"] = "Es konnten keine Modellparameter ermittelt werden"
        return model_params
