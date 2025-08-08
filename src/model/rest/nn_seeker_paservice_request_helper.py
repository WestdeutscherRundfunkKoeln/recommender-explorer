import logging
from urllib3 import PoolManager, Retry
import json

logger = logging.getLogger(__name__)

class RequestHelper:
    def __init__(self):
        self._endpoint = ""
        self._model_props = {}

        self._http = self._init_http_pool()

    def _init_http_pool(self):
        retries = Retry(
            connect= 5,
            read= 2,
            redirect= 5,
            backoff_factor= 0.1,
        )
        return PoolManager(retries=retries)

    def set_model_config(self, model_config, endpoint_key="endpoint", props_key="properties"):
        self._endpoint = model_config.get(endpoint_key, None)
        self._model_props = model_config.get(props_key, None)
        if not self._endpoint:
            raise ValueError(f"Invalid model configuration: '{endpoint_key}' is required but missing or empty.")

        if not self._model_props or not isinstance(self._model_props, dict):
            raise ValueError(f"Invalid model configuration: '{props_key}' is required and must be a dictionary.")

    def get_headers(self):
        if not self._model_props:
            raise ValueError("Model properties not set")
        return {self._model_props["auth_header"]: self._model_props["auth_header_value"]}

    def get(self, endpoint: str | None = None, headers: dict | None = None):
        endpoint = self._endpoint if endpoint is None else endpoint
        print("last")
        print(endpoint)
        print("last")
        headers = self.get_headers() if headers is None else headers
        logger.info(f"GET call to [{endpoint}]")
        response = self._http.request("GET", endpoint, headers=headers)
        status = response.status
        data = response.data.decode("utf-8")
        logger.info(f"Got status {status} with data: {data}")
        data_str = json.loads(data)
        return status, data_str

    def post(self, endpoint: str | None = None, headers: dict | None = None, json_body: dict | None = None):
        import json

        endpoint = endpoint or self._endpoint
        headers = headers or self.get_headers()
        json_body = json_body or {}
        logger.info(f"POST call to [{endpoint}] with body {json.dumps(json_body)}")
        response = self._http.request("POST", endpoint, headers=headers, json=json_body)
        status = response.status
        data = response.data.decode("utf-8")
        logger.info(f"Got status {status} with data: {data}")
        return status, data

    def get_model_props(self):
        return self._model_props
