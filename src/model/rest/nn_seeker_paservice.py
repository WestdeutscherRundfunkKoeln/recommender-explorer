import logging
import constants

from model.rest.nn_seeker_rest import NnSeekerRest
from dto.item import ItemDto
from util.dto_utils import get_primary_idents

logger = logging.getLogger(__name__)

class NnSeekerPaService(NnSeekerRest):

    ITEM_IDENTIFIER_PROP = 'externalid'

    def __init__( self, config ):

        self.__max_num_neighbours = 16
        self.__configuration_c2c = "relatedItems"
        self.__configuration_u2c = "forYou"
        self.__explain = False
        # TODO: this can probably be removed when primary key handling is depricated after ingest micro service deployment
        self.__config = config
        self.__model_config = {}
        super().__init__()

    def get_k_NN(self, item: ItemDto, k, nn_filter) -> tuple[list, list, str]:
        primary_ident, oss_field = get_primary_idents(self.__config)
        content_id =  item.__getattribute__(oss_field)
        model_props = self.__model_config['properties']
        headers = {
            model_props['auth_header']: model_props['auth_header_value']
        }

        params = {
            "configuration": self.__configuration_c2c,
            "limit": self.__max_num_neighbours,
            "assetId": content_id
        }

        status, pa_recos = super().post_2_endpoint(self.__model_config['endpoint'], headers, params)

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

        return recomm_content_ids, nn_dists, oss_field

    def get_recos_user(self, user, n_recos):
        model_props = self.__model_config['properties']

        user_id = user.id
        headers = {
            model_props['auth_header']: model_props['auth_header_value']
        }
        params = {
            "configuration": self.__configuration_u2c,
            "explain": True,
            "userId": user_id
        }

        params["modelType"] = model_props["param_model_type"] if model_props["param_model_type"] else ''

        status, pa_recos = super().post_2_endpoint(self.__model_config['endpoint'], headers, params)

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
            logger.warning('discarding not found item [' + params['assetId'] + ']')

        return recomm_content_ids, nn_dists, self.ITEM_IDENTIFIER_PROP

    def get_max_num_neighbours(self, content_id):
        return self.__max_num_neighbours

    def set_model_config(self, model_config):
        self.__model_config = model_config

    def get_model_params(self):
        model_params = {}
        model_params['Error'] = 'Es konnten keine Modellparameter ermittelt werden'
        return model_params