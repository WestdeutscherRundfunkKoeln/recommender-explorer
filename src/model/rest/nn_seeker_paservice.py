import logging

from model.rest.nn_seeker_rest import NnSeekerRest

logger = logging.getLogger(__name__)

class NnSeekerPaService(NnSeekerRest):

    ITEM_IDENTIFIER_PROP = 'externalid'

    def __init__( self, config ):

        self.__max_num_neighbours = 16
        self.__base_uri = ''
        self.__configuration_c2c = "zdfRecosOn"
        self.__configuration_u2c = "forYou"
        self.__explain = False
        super().__init__()

    def get_k_NN(self, item, k, nn_filter):
        content_id = item['crid']
        headers = {
            "ARD": "access"
        }
        params = {
            "configuration": self.__configuration_c2c,
            "limit": self.__max_num_neighbours,
            "assetId": content_id
        }

        status, pa_recos = super().post_2_endpoint(self.__base_uri, headers, params)

        recomm_content_ids = []
        nn_dists = []

        #
        # add better status and error handling
        #
        if status == 200:
            for reco in pa_recos['recommendations']:
                nn_dists.append(reco['score'])
                recomm_content_ids.append(reco['asset']['assetId'])
        else:
            logger.warning('discarding not found item [' + params['assetId'] + ']')

        return recomm_content_ids, nn_dists, self.ITEM_IDENTIFIER_PROP

    def get_recos_user(self, user, n_recos):

        user_id = user.id
        headers = {
            "ARD": "access"
        }
        params = {
            "configuration": self.__configuration_u2c,
            "explain": True,
            "userId": 1 #user_id
        }

        status, pa_recos = super().post_2_endpoint(self.__base_uri, headers, params)

        recomm_content_ids = []
        nn_dists = []

        #
        # add better status and error handling
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

    def set_endpoint(self, endpoint):
        self.__base_uri = endpoint

    def get_model_params(self):
        model_params = {}
        model_params['Error'] = 'Es konnten keine Modellparameter ermittelt werden'
        return model_params