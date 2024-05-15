import os
from datetime import datetime, timedelta

from opensearchpy import OpenSearch, RequestsHttpConnection

OSS_HOST = os.environ.get("OPENSEARCH_HOST")
OSS_USER = os.environ.get("OPENSEARCH_USER")
OSS_PASS = os.environ.get("OPENSEARCH_PASS")


def initialize_oss_client():
    client = OpenSearch(
        hosts=[{"host": OSS_HOST, "port": 443}],
        http_auth=(OSS_USER, OSS_PASS),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=600,
    )

    return client


def delete_oss_index(oss_client, idx_name):
    try:
        print(idx_name, "will be deleted")
        oss_client.indices.delete(idx_name)
    except Exception:
        print("non existing")


def clean_indices(oss_client):
    idx_info = oss_client.indices.get_alias("reco_pa_prod_idx*")
    idx_list = list(idx_info.keys())
    idx_list.sort()

    seven_days_ago = datetime.today() - timedelta(days=7)

    for idx_name in idx_list:
        date_str = idx_name[17:25]
        date = datetime.strptime(date_str, "%Y%m%d")
        if date < seven_days_ago:
            delete_oss_index(oss_client, idx_name)


if __name__ == "__main__":
    clean_indices(initialize_oss_client())
