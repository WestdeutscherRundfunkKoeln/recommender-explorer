import json
import logging

from model.nn_seeker import NnSeeker
from urllib3 import Retry, PoolManager, ProxyManager

logger = logging.getLogger(__name__)

class NnSeekerRest(NnSeeker):

    def __init__(self):
        self.__retry_connection = 5
        self.__retry_reads = 2
        self.__retry_redirects = 5
        self.__backoff_factor = 0.1

    def post_2_endpoint( self, base_uri, headers, post_params ):
        retries = Retry(
            connect=self.__retry_connection,
            read=self.__retry_reads,
            redirect=self.__retry_redirects,
            backoff_factor=self.__backoff_factor
        )

        http = ProxyManager(proxy_url='http://proxy.wdr.de:8080', retries=retries)
        # http = PoolManager(retries=retries)

        logger.warning('calling [' + base_uri + '] with params ' + json.dumps(post_params))

        response = http.request('POST', base_uri, fields=post_params, headers=headers)
        status_code = response.status
        data = json.loads(response.data.decode('utf-8'))
        return status_code, data
