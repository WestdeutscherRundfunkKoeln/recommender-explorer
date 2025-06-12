from typing import Any
from dto.item import ItemDto
from model.rest.nn_seeker_rest import NnSeekerRest


class NnSeekerPaServiceSearch(NnSeekerRest):
    def _get_request_params_c2c_s2c(self, item: ItemDto, oss_field: str) -> dict[str, Any]:
        # Add the Client
        return {
            "embedText": item.description, "client": item.client,
        }

    @staticmethod
    def _parse_response(response: dict[str, Any]) -> tuple[list[str], list[float], list[Any]]:
        recomm_content_ids = []
        nn_dists = []
        for reco in response["items"]:
            nn_dists.append(reco["score"])
            recomm_content_ids.append(reco["id"])

        utilities = response.get("utilities", [])

        return recomm_content_ids, nn_dists, utilities
