import logging
from urllib3 import PoolManager, Retry

logger = logging.getLogger(__name__)

class RequestHelper:
    def __init__(self):
        self._endpoint = ""
        self._model_props = {}

        self._retry_connection = 5
        self._retry_reads = 2
        self._retry_redirects = 5
        self._backoff_factor = 0.1

        self._http = self._init_http_pool()

    def _init_http_pool(self):
        retries = Retry(
            connect=self._retry_connection,
            read=self._retry_reads,
            redirect=self._retry_redirects,
            backoff_factor=self._backoff_factor,
        )
        return PoolManager(retries=retries)

    def set_model_config(self, model_config, endpoint_key="endpoint", props_key="properties"):
        self._endpoint = model_config.get(endpoint_key, "")
        self._model_props = model_config.get(props_key, {})

    def get_headers(self):
        if not self._model_props:
            raise ValueError("Model properties not set")
        return {self._model_props["auth_header"]: self._model_props["auth_header_value"]}

    def get(self, endpoint: str | None = None, headers: dict | None = None):
        endpoint = endpoint or self._endpoint
        headers = headers or self.get_headers()
        logger.info(f"GET call to [{endpoint}]")
        response = self._http.request("GET", endpoint, headers=headers)
        status = response.status
        data = response.data.decode("utf-8")
        logger.info(f"Got status {status} with data: {data}")
        return status, data

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
