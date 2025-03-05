from typing import Any
from dto.item import ItemDto
from model.rest.nn_seeker_rest import NnSeekerRest


class NnSeekerPaServiceNews(NnSeekerRest):
    def _get_request_params_c2c(self, item: ItemDto, oss_field: str) -> dict[str, Any]:
        return {
            "referenceId": item.__getattribute__(oss_field),
            "reco": False,
        }

    @staticmethod
    def _parse_response(response: dict[str, Any]) -> tuple[list[str], list[float]]:
        recomm_content_ids = []
        nn_dists = []
        for reco in response["items"]:
            nn_dists.append(reco["score"])
            recomm_content_ids.append(reco["id"])
        return recomm_content_ids, nn_dists
