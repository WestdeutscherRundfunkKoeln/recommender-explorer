import re
import logging
import json
import constants

from model.u2c_seeker import U2CSeeker
from boto3 import client as boto3client
from botocore.exceptions import ClientError
from exceptions.endpoint_error import EndpointError
from exceptions.user_not_found_error import UnknownUserError
from urllib.parse import urlparse
from dto.user_item import UserItemDto

logger = logging.getLogger(__name__)

class CollabModelClient(U2CSeeker):

    ITEM_IDENTIFIER_PROP = 'externalid'

    def __init__( self, config ):
        self.__num_recos = 16
        self.__model_config = {}
 
        cross_account_options = self.__get_cross_account_options(
            config[constants.MODEL_CONFIG_U2C][constants.MODEL_TYPE_U2C]['ARD-ALS-Experiments']['role_arn']
        )
        self.__sm_run_client = boto3client("sagemaker-runtime", **cross_account_options)
        self.__sm_client = boto3client("sagemaker", **cross_account_options)
        self.__s3_client = boto3client('s3', **cross_account_options)

        self.model_properties = {}
        self.step_reports = {
            'Evaluate-ARDCollabMatrix': {
                'report-file': 'evaluation',
                'reducer': 'binary_classification_metrics'
            },
            'Preprocess-ARDCollabMatrix': {
                'report-file': 'preprocessing',
                'reducer': False
            }

        }

    def get_recos_user(self, user_item: UserItemDto, num_recos: int, reco_filter: dict[str, Any] = False) -> tuple[list, list, str]:

        json_body = json.dumps({
            "userId": user_item.id,
            "numberOfItems": num_recos
        })

        try:
            logger.info('Invoking endpoint call to [' + self.__model_config['endpoint'] + '] for user_id [' + user_item.id + ']')
            response = self.__sm_run_client.invoke_endpoint(
                EndpointName=self.__model_config['endpoint'].removeprefix("sagemaker://"),
                Body=json_body,
                ContentType="application/json",
            )
            response_data = json.loads(response["Body"].read().decode("utf-8"))
            if response_data.get('message', '').startswith("Unknown userId"):
                raise UnknownUserError("Keine Empfehlungen für den Benutzer [" + user_item.id + "] in diesem Modell", {})
            reco_ids = [hit['id'] for hit in response_data['recommendations']]
            reco_scores = [hit['score'] for hit in response_data['recommendations']]
            return reco_ids, reco_scores, self.ITEM_IDENTIFIER_PROP

        except UnknownUserError as e:
            raise(e)
        except Exception as e:
            logging.error(e)
            raise EndpointError("Couldn't get a response from endpoint [" + self.__model_config['endpoint'] + ']', {})

    def set_model_config(self, model_config):
        self.__model_config = model_config

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


