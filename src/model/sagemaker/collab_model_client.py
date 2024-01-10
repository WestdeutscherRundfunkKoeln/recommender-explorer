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
        self.__endpoint = ''
 
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

    def get_recos_user(self, user_item: UserItemDto, num_recos: int) -> tuple[list, list, str]:

        json_body = json.dumps({
            "userId": user_item.id,
            "numberOfItems": num_recos
        })

        try:
            logger.info('Invoking endpoint call to [' + self.__endpoint + '] for user_id [' + user_item.id + ']')
            response = self.__sm_run_client.invoke_endpoint(
                EndpointName=self.__endpoint.removeprefix("sagemaker://"),
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
            raise EndpointError("Couldn't get a response from endpoint [" + self.__endpoint + ']', {})

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

    
    def get_model_params(self):
        try:
            # Get the model name, model description from endpoint of this model
            endpoint_details = self.__sm_client.describe_endpoint(EndpointName=self.__endpoint.removeprefix("sagemaker://"))
            endpoint_description = self.__sm_client.describe_endpoint_config(EndpointConfigName=endpoint_details["EndpointConfigName"])
            model_name = endpoint_description['ProductionVariants'][0]['ModelName']

            # get model description and model package name from model
            model_description = self.__sm_client.describe_model(ModelName=model_name)
            model_package_name = model_description['PrimaryContainer']['ModelPackageName']
            model_package_description = self.__sm_client.describe_model_package(ModelPackageName=model_package_name)
            model_description  = model_package_description['ModelPackageDescription']
            model_creation_timestamp =  model_package_description['CreationTime']
            self.model_properties['Metadata'] = {}
            self.model_properties['Metadata']['description'] = model_description
            self.model_properties['Metadata']['created'] = model_creation_timestamp

            # now we're ready to retrieve the pipeline_arn, execution_id and training job descriptors
            model_data_url = model_package_description['InferenceSpecification']['Containers'][0]['ModelDataUrl']
            res = re.search("^.*\/(.*)/output/model.tar.gz$", model_data_url)
            train_job_descriptor = res.group(1)
            res = re.search("^(.*?)-", train_job_descriptor)
            execution_id = res.group(1)
            pipeline_arn = model_package_description['MetadataProperties']['GeneratedBy']
            logger.info('Found a pipeline execution id [' + execution_id + ']')

            # given the pipeline arn, retrieve the pipeline definition and experiment name
            pipeline_execution_description = self.__sm_client.describe_pipeline_definition_for_execution(
                PipelineExecutionArn=pipeline_arn)
            pipeline_definition = json.loads(pipeline_execution_description['PipelineDefinition'])

            # given the pipeline infos, get the preprocessing infos
            self.__retrieve_processing_reports(pipeline_definition, execution_id)

            # given the pipeline infos, get the training infos
            self.__retrieve_training_properties(train_job_descriptor)

        except Exception as e:
            logger.warning("Fehler beim Ermitteln der Modell-Parameter [" + str(e) + ']')
            self.model_properties['Error'] = 'Es ist ein Fehler beim Ermitteln der Modellparameter aufgetreten'

        return self.model_properties

    def __retrieve_processing_reports(self, pipeline_definition, execution_id):

        for step in pipeline_definition['Steps']:
            step_name = step['Name']
            if step_name in self.step_reports.keys():
                step_arguments = step['Arguments']
                step_outputs = step_arguments['ProcessingOutputConfig']['Outputs']

                for output in step_outputs:
                    if output['OutputName'] == self.step_reports[step_name]['report-file']:
                        s3_obj = output['S3Output']['S3Uri']

                s3_uri = ''
                for url_part in s3_obj['Std:Join']['Values']:
                    if isinstance(url_part, str):
                        s3_uri = s3_uri + url_part + '/'
                    elif isinstance(url_part, dict):
                        s3_uri = s3_uri + execution_id + '/'

                s3_uri = s3_uri + self.step_reports[step_name]['report-file'] + '.json'

                o = urlparse(s3_uri, allow_fragments=False)
                s3_response = self.__s3_client.get_object(
                    Bucket=o.netloc,
                    Key=o.path.removeprefix('/')
                )

                s3_object_body = s3_response.get('Body')
                content = self.__reduce_dct(json.loads(s3_object_body.read()), step_name)
                self.model_properties[step_name] = content

    def __reduce_dct(self, dct, step):
        r = self.step_reports[step]['reducer']
        reduced = {}
        if r:
            for k,v in dct[r].items():
                reduced[k] = v['value']
            return reduced
        else:
            return dct

    def __retrieve_training_properties(self, train_job_descriptor):
        trial_component_description = self.__sm_client.describe_trial_component(TrialComponentName=train_job_descriptor + "-aws-training-job")
        trial_parameters = trial_component_description['Parameters']

        self.model_properties['Trainings-Metriken'] = {}
        self.model_properties['Trainings-Metriken']['Zielmetrik-Name'] = trial_parameters['_tuning_objective_metric']['StringValue']
        self.model_properties['Tuning-Hyperparameter'] = {}
        self.model_properties['Tuning-Hyperparameter']['alpha'] = trial_parameters['alpha']['NumberValue']
        self.model_properties['Tuning-Hyperparameter']['factors'] = trial_parameters['factors']['NumberValue']
        self.model_properties['Tuning-Hyperparameter']['regularization'] = trial_parameters['regularization']['NumberValue']
        self.model_properties['Statische Hyperparameter'] = {}
        hpo_params = json.loads(trial_parameters['hpo_params']['StringValue'])
        self.model_properties['Statische Hyperparameter']['Coverage-Gewicht'] = hpo_params['coverage_weight']
        self.model_properties['Statische Hyperparameter']['Watchtime-Gewicht'] = hpo_params['watchtime_weight']
        self.model_properties['Statische Hyperparameter']['Random State'] = hpo_params['random_state']
