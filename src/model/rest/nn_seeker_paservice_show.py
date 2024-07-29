import logging
import constants
import traceback


from model.rest.nn_seeker_paservice import NnSeekerPaService
from model.opensearch.base_data_accessor_opensearch import BaseDataAccessorOpenSearch
from dto.content_item import ContentItemDto
from util.dto_utils import dto_from_classname
from exceptions.item_not_found_error import UnknownItemError
from exceptions.user_not_found_error import UnknownUserError

logger = logging.getLogger(__name__)

class NnSeekerPaServiceShow(NnSeekerPaService):
    def __init__( self, config ):

        self.__max_num_neighbours = 16
        self.__configuration_u2c = "forYou"
        self.__explain = False
        self.__model_config = {}
        self.__item_accessor = BaseDataAccessorOpenSearch(config)

        self.__config = config
        super().__init__(config)

    def get_recos_user(self, user, n_recos, nn_filter=False):
        reco_ids, nn_dists, oss_field = super().get_recos_user(user, n_recos, nn_filter)
        for idx, show_id in enumerate(reco_ids):
            item_dto = dto_from_classname(
                class_name='ShowItemDto',
                position=constants.ITEM_POSITION_RECO,
                item_type=constants.ITEM_TYPE_CONTENT,
                provenance=constants.ITEM_PROVENANCE_C2C,
            )
            lookup_res = self.__item_accessor.get_item_by_urn(item_dto, show_id)
            logger.info('Replacing show id [' + show_id + '] at idx position [' + str(idx) + '] with corresponding episode id [' +
                        lookup_res[0][0].episode + ']')
            reco_ids[idx] = lookup_res[0][0].episode

        return reco_ids, nn_dists, oss_field

