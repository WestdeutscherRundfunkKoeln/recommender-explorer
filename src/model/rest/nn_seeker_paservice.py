import logging
import constants

from typing import Any
from model.rest.nn_seeker_rest import NnSeekerRest
from dto.item import ItemDto
from dto.user_item import UserItemDto
from util.dto_utils import get_primary_idents
from exceptions.item_not_found_error import UnknownItemError
from exceptions.user_not_found_error import UnknownUserError

logger = logging.getLogger(__name__)

class NnSeekerPaService(NnSeekerRest):

    def __init__( self, config ):

        self.__max_num_neighbours = 16
        self.__configuration_c2c = "relatedItems"
        self.__configuration_u2c = "forYou"
        self.__explain = False
        self.__model_config = {}

        # TODO: this can probably be removed when primary key handling is depricated after ingest micro service deployment
        self.__config = config
        super().__init__()

    def get_k_NN(self, item: ItemDto, k, nn_filter) -> tuple[list, list, str]:
        primary_ident, oss_field = get_primary_idents(self.__config)
        content_id =  item.__getattribute__(oss_field)
        model_props = self.__model_config['properties']
        headers = {
            model_props['auth_header']: model_props['auth_header_value']
        }


        ## static args
        params = {
            "configuration": self.__configuration_c2c,
            "assetId": content_id,
            "limit": self.__max_num_neighbours
        }

        ## any other args are taken verbatim from config
        for prop in model_props:
            prop_short = prop.removeprefix('param_')
            if prop not in params:
                params[prop_short] = model_props[prop]


        status, pa_recos = super().post_2_endpoint(self.__model_config['endpoint'], headers, params)

        logger.info('Got status code [' + str(status) + '] and data: ')
        logger.info(pa_recos)

        recomm_content_ids = []
        nn_dists = []



        #
        # TODO - add better status and error handling
        #
        if status == 200:
            for reco in pa_recos['recommendations']:
                nn_dists.append(reco['score'])
                recomm_content_ids.append(reco['asset']['assetId'])
        else:
            logger.warning('Got status code [' + str(status) + ']. Discarding this item [' + params['assetId'] + ']')
            raise UnknownItemError('Item with primary id [' + content_id + '] not found in endpoint [' + self.__model_config['endpoint'] + ']', {})

        return recomm_content_ids, nn_dists, oss_field

    def get_recos_user(self, user: UserItemDto, n_recos:int, nn_filter: dict[str, Any] = False) -> tuple[list, list, str]:
        primary_ident, oss_field = get_primary_idents(self.__config)
        model_props = self.__model_config['properties']

        user_id = user.id
        headers = {
            model_props['auth_header']: model_props['auth_header_value']
        }

        params = {
            "configuration": self.__configuration_u2c,
            "explain": True,
            "userId": user_id,
        }

        ## any other args are taken verbatim from config
        for prop in model_props:
            prop_short = prop.removeprefix('param_')
            if prop not in params:
                params[prop_short] = model_props[prop]


        selected_params = {}
        if nn_filter and "editorialCategories" in nn_filter and len(nn_filter["editorialCategories"]) > 0:
            selected_params["includedCategories"] = ",".join(nn_filter["editorialCategories"])

        all_params = {**params, **selected_params}

        status, pa_recos = super().post_2_endpoint(self.__model_config['endpoint'], headers, all_params)

        recomm_content_ids = []
        nn_dists = []

        logger.info('Got status code [' + str(status) + '] and data: ')
        logger.info(pa_recos)

        #
        # TODO - add better status and error handling
        #
        if status == 200:
            for reco in pa_recos['recommendations']:
                nn_dists.append(reco['score'])
                recomm_content_ids.append(reco['asset']['assetId'])
        else:
            logger.warning('Got status code [' + str(status) + ']. Discarding this user [' + user_id + ']')
            raise UnknownUserError('User with primary id [' + user_id + '] not found in endpoint [' + self.__model_config['endpoint'] + ']', {})

        return recomm_content_ids, nn_dists, oss_field

    def get_max_num_neighbours(self, content_id):
        return self.__max_num_neighbours

    def set_model_config(self, model_config):
        self.__model_config = model_config

    def get_model_params(self):
        model_params = {}
        model_params['Error'] = 'Es konnten keine Modellparameter ermittelt werden'
        return model_params
