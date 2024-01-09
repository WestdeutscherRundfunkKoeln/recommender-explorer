import logging
import json

from boto3 import client as boto3client
from exceptions.endpoint_error import EndpointError
from exceptions.user_not_found_error import UnknownUserError

logger = logging.getLogger(__name__)

class ClusteringModelClient:

    def __init__( self, config ):
        self.__endpoint = ''
        self._client = boto3client("sagemaker-runtime")

    def get_user_cluster(self):

        json_body = json.dumps({ "action": "list_clusters" })

        try:
            logger.info('Invoking endpoint call to [' + self.__endpoint + ']')
            response = self._client.invoke_endpoint(
                EndpointName=self.__endpoint.removeprefix("sagemaker://"),
                Body=json_body,
                ContentType="application/json",
            )
        except Exception as e:
            logging.error(e)
            raise EndpointError("Couldn't get a response from endpoint [" + self.__endpoint + ']')

        response_data = json.loads(response["Body"].read().decode("utf-8"))
        user_cluster = {}
        for one_cluster in response_data['clusters']:
            user_cluster[one_cluster['label']] = one_cluster['userids']
        return user_cluster

    def get_users_by_category(self, genreCategory):

        body_dict = {
            "action": "filter_users",
            "params":{
                "filters": [ {
                    "column": "genreCategory",
                    "value": genreCategory
                }]
            }
        }

        json_body = json.dumps(body_dict)

        try:
            logger.info('Invoking endpoint call to [' + self.__endpoint + ']')
            response = self._client.invoke_endpoint(
                EndpointName=self.__endpoint.removeprefix("sagemaker://"),
                Body=json_body,
                ContentType="application/json",
            )
        except Exception as e:
            logging.error(e)
            raise EndpointError("Couldn't get a response from endpoint [" + self.__endpoint + ']', {})

        response_data = json.loads(response["Body"].read().decode("utf-8"))
        if not len(response_data):
            raise UnknownUserError("Momentan gibt es keine Benutzer, die in erster Linie das Genre [" + genreCategory + "]" + " konsumieren", {})
        user_cluster = {}
        user_cluster[genreCategory] = response_data
        return user_cluster

    def set_endpoint(self, endpoint):
        self.__endpoint = endpoint