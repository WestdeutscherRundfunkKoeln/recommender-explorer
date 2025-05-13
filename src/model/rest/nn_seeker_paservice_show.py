import logging

import constants
from model.opensearch.base_data_accessor_opensearch import BaseDataAccessorOpenSearch
from model.rest.nn_seeker_paservice import NnSeekerPaService
from util.dto_utils import dto_from_classname

logger = logging.getLogger(__name__)


class NnSeekerPaServiceShow(NnSeekerPaService):
    def __init__(self, config, item_accessor: BaseDataAccessorOpenSearch):
        self.__item_accessor = item_accessor

        super().__init__(config)

    @classmethod
    def from_config(cls, config):
        return cls(config, BaseDataAccessorOpenSearch(config))

    def get_recos_user(self, user, n_recos, nn_filter=False):
        reco_ids, nn_dists, oss_field, utilities = super().get_recos_user(user, n_recos, nn_filter)
        for idx, show_id in enumerate(reco_ids):
            item_dto = dto_from_classname(
                class_name="ShowItemDto",
                position=constants.ITEM_POSITION_RECO,
                item_type=constants.ITEM_TYPE_CONTENT,
                provenance=constants.ITEM_PROVENANCE_C2C,
            )
            lookup_res = self.__item_accessor.get_item_by_urn(item_dto, show_id)
            logger.info(
                "Replacing show id ["
                + show_id
                + "] at idx position ["
                + str(idx)
                + "] with corresponding episode id ["
                + lookup_res[0][0].episode
                + "]"
            )
            reco_ids[idx] = lookup_res[0][0].episode

        utilities = None

        return reco_ids, nn_dists, oss_field, utilities
