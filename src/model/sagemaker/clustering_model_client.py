import logging
import json
import constants

from boto3 import client as boto3client
from exceptions.endpoint_error import EndpointError
from exceptions.user_not_found_error import UnknownUserError

logger = logging.getLogger(__name__)

class ClusteringModelClient:

    def __init__( self, config ):
        self.__endpoint = ''
        cross_account_options = self.__get_cross_account_options(
            config[constants.MODEL_CONFIG_U2C]['clustering_models']['U2C-Knn-Model']['role_arn']
        )
        self._client = boto3client("sagemaker-runtime", **cross_account_options)

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

    def __get_cross_account_options(self, role_arn):
        sts_client = boto3client("sts")
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn, RoleSessionName="RecoExplorerU2C"
        )
        return {
            "aws_access_key_id": assumed_role["Credentials"]["AccessKeyId"],
            "aws_secret_access_key": assumed_role["Credentials"]["SecretAccessKey"],
            "aws_session_token": assumed_role["Credentials"]["SessionToken"],
            "region_name": "eu-central-1"
        }
