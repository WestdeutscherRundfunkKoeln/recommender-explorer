from opensearchpy import OpenSearch, RequestsHttpConnection, helpers
import logging
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


class OssAccessor:

    def __init__(self, config):
        self.target_idx_name = config['opensearch']['index']

        host = config['opensearch']['host']
        auth = (config['opensearch']['user'],
                config['opensearch']['pass'])
        port = config['opensearch']['port']

        logger.info('Host: ' + host)

        # initialize OSS client
        self.oss_client = OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=600,
        )

    def create_oss_doc(self, data):
        # add document to index
        response = self.oss_client.index(
            index=self.target_idx_name,
            body=data,
            id=f"{data['id']}",
            refresh=True
        )

        logger.info('Response: ' + json.dumps(response, indent=4, default=str))

        return response

    def delete_oss_doc(self, id):
        response = self.oss_client.delete(
            index=self.target_idx_name,
            id=id
        )
        return response