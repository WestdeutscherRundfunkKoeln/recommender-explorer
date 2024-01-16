import json
from datetime import datetime
import numpy as np
import pandas as pd
from opensearchpy import OpenSearch, RequestsHttpConnection, helpers
import itertools
import datetime
import boto3
import logging
import os
import datetime
from tqdm import tqdm
from hashlib import sha256
from oss_utils import ModelConfig, Embedder, safe_value, get_approx_knn_mapping

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


S3_BUCKET = 'dateneinheiten-ard-recommender-test'

# mediathek
#S3_BASE_PA_DATA_FILE = 'paservice/ard_content_prod_latest.json.gz'
#S3_SUBGENRE_LUT_FILE = 'paservice/ard_luts/mediathek_subgenre_lut_2023-02-21.json'
#S3_THEMATIC_LUT_FILE = 'paservice/ard_luts/mediathek_thematic_lut_2023-02-21.json'

# audiothek
S3_BASE_PA_DATA_FILE = 'at-paservice/audiothek_content_prod_latest.json.gz'
S3_SUBGENRE_LUT_FILE = 'at-paservice/ard_luts/audiothek_subgenre_lut_2024_01_11.json'
S3_THEMATIC_LUT_FILE = 'at-paservice/ard_luts/audiothek_thematic_lut_2024_01_11.json'


#SAMPLE_SIZE = 1000
SAMPLE_SIZE = 1000


def load_and_preprocess_data(s3_bucket,
                             s3_base_pa_data_filename,
                             s3_subgenre_lut_file,
                             s3_thematic_lut_file,
                             sample=True):
    # read data
    res = "s3://{}/{}".format(s3_bucket, s3_base_pa_data_filename)
    df = pd.read_json(res, lines=True, compression='gzip')

    if sample:
        print("Sampling " + str(SAMPLE_SIZE) + " items")
        df = df.iloc[0:SAMPLE_SIZE].copy()
    else:
        print("Processing full dataset")

    df["availableFrom"] = pd.to_datetime(
        df["availableFrom"], errors="coerce", utc=True
    ).fillna(pd.Timestamp("2099-12-31T00:00:00Z"))
    df["availableTo"] = pd.to_datetime(df["availableTo"], errors="coerce", utc=True).fillna(
        pd.Timestamp("2099-12-31T00:00:00Z")
    )

    # decode IDs in subgenre and thematic cats
    s3 = boto3.resource('s3')

    subgenre_obj = s3.Object(s3_bucket, s3_subgenre_lut_file)
    subgenre_lut = json.load(subgenre_obj.get()['Body'])

    thematic_obj = s3.Object(s3_bucket, s3_thematic_lut_file)
    thematic_lut = json.load(thematic_obj.get()['Body'])
    df["embedText"] = df["title"] + ". " + df["description"]
    df["embedTextHash"] = [
        sha256(text.encode("utf-8")).hexdigest() for text in df["embedText"]
    ]

    df["subgenreCategoriesIds"] = df["subgenreCategories"]
    df["thematicCategoriesIds"] = df["thematicCategories"]

    # df.loc['subgenreCategories'].apply([lambda catid: subgenre_lut[catid]] )

    df["subgenreCategories"] = df.subgenreCategoriesIds.apply(
        lambda row: [subgenre_lut[v] for v in row if subgenre_lut.get(v)]
    )
    df["thematicCategories"] = df.thematicCategoriesIds.apply(
        lambda row: [thematic_lut[v] for v in row if thematic_lut.get(v)]
    )

    return df


def calc_embeddings(df):
    model_names = [
        'T-Systems-onsite/german-roberta-sentence-transformer-v2',
        'all-MiniLM-L6-v2',
        'sentence-transformers/distiluse-base-multilingual-cased-v1'  # ZDF
    ]
    inc_titles = [True]
    inc_descs = [True]
    inc_keywords = [False]

    config_opts = itertools.product(
        model_names, inc_titles, inc_descs, inc_keywords)
    configs = []

    for model_name, inc_title, inc_desc, inc_keyword in config_opts:
        cfg = ModelConfig(model_prefix=None, model_name=model_name, include_title=inc_title,
                          include_description=inc_desc, include_keywords=inc_keyword)
        configs.append(cfg)

    embedding_field_names = []
    embedding_sizes = []

    for model_config in tqdm(configs, desc='Model configs', position=0, leave=False):

        model = Embedder(model_config)

        result = model.calulate_data_embeddings(df)
        embeddings_df = pd.DataFrame.from_dict(
            result["embeddings"], orient="index")

        # get size of embedding
        emb_size = len(embeddings_df['embedding'][0])
        embedding_sizes.append(emb_size)

        fieldname = model_config.getStr()  # .replace('/','_')
        embedding_field_names.append(fieldname)

        embeddings_df = embeddings_df.rename(columns={"embedding": fieldname})
        df = pd.merge(df, embeddings_df[['id', fieldname]], on=[
                          "id"], how='left')

    return df, embedding_field_names, embedding_sizes


def postprocess_data(df):
    # fix date types
    df["availableFrom"] = pd.to_datetime(
        df["availableFrom"], errors="coerce", utc=True
    ).fillna(pd.Timestamp("2099-12-31T00:00:00Z"))
    
    df["availableTo"] = pd.to_datetime(
        df["availableTo"], errors="coerce", utc=True
    ).fillna(pd.Timestamp("2099-12-31T00:00:00Z"))

    df["startDate"] = pd.to_datetime(
        df["availableTo"], errors="coerce", utc=True
    ).fillna(pd.Timestamp("2099-12-31T00:00:00Z"))

    has_col_naval = df.isna().any()
    nacols = has_col_naval[has_col_naval == True].index

    for col in nacols:
        logger.info(f"Col {col} has null vals fixing")
        df[col] = df[col].apply(safe_value)

    return df


def delete_oss_index(client, idx_name):
    try:
        client.indices.delete(idx_name)
    except:
        logger.info("non existing")
        
        
def filterKeys(document, keys):
    return {key: document[key] for key in keys}


def doc_generator(df, index_name, keys):
    df_iter = df.iterrows()
    for index, document in df_iter:
        yield {
            "_index": index_name,
            "_type": "_doc",
            "_id": f"{document['id']}",
            "_source": filterKeys(document, keys),
        }
    # raise StopIteration
    

def upload_data_oss(df, client, embedding_field_names, embedding_sizes, index_prefix="reco_pa_test"):
    # Determine target index name by timestamp
    ts = datetime.datetime.utcnow().strftime('%Y%m%d_%H_%M')
    target_idx_name = index_prefix + '_idx_'+ts
    current_idx_alias = index_prefix + '_idx_current'
    logger.info(f"Target index name: {target_idx_name}")
    logger.info(f"Target index alias: {current_idx_alias}")

    # make sure the index doesn't exists yet
    delete_oss_index(client, target_idx_name)

    idx_create_body_approx = get_approx_knn_mapping(
        embedding_field_names, embedding_sizes)
    
    client.indices.create(target_idx_name, body=idx_create_body_approx)

    # transfer all columns, we could subset here
    use_these_keys = df.columns.tolist()
    
    # Set total number of documents
    number_of_docs = df.shape[0]

    progress = tqdm(unit="docs", total=number_of_docs,
                    leave=True, desc="indexing")
    successes = 0

    for ok, action in helpers.streaming_bulk(
        client=client,
        index=target_idx_name,
        actions=doc_generator(df, target_idx_name, use_these_keys),
    ):
        progress.update(1)
        successes += ok

    # re-link current alias to this index
    is_cur_alias_exist = client.indices.exists_alias(name=current_idx_alias)
    
    if not is_cur_alias_exist:
        logger.info("create alias with current index")
        client.indices.put_alias(name=current_idx_alias, index=target_idx_name)
    else:
        logger.info("Delete alias")
        client.indices.delete_alias(
            name=current_idx_alias, index=index_prefix + '_*')
        client.indices.put_alias(name=current_idx_alias, index=target_idx_name)

        
if __name__ == "__main__":
    index_sample = os.environ.get('INDEX_SAMPLE') == 'True'
    index_prefix = os.environ.get('INDEX_PREFIX')
    logger.info(f"Index sample: {index_sample}")
    logger.info(f"Index prefix: {index_prefix}")


    host = os.environ.get('OPENSEARCH_HOST')
    auth = (os.environ.get('OPENSEARCH_USER'),
            os.environ.get('OPENSEARCH_PASS'))

    logger.info('Host: ' + host)

    logger.info("Preprocess data")
    df = load_and_preprocess_data(S3_BUCKET, 
                                  S3_BASE_PA_DATA_FILE, 
                                  S3_SUBGENRE_LUT_FILE, 
                                  S3_THEMATIC_LUT_FILE, 
                                  index_sample)


    logger.info("Calculate embeddings")
    df, embedding_field_names, embedding_sizes = calc_embeddings(df)
    
    logger.info("Postprocess data")
    df = postprocess_data(df)

    print(df["subgenreCategories"])

    # initialize OSS client
    oss_client = OpenSearch(
        hosts=[{"host": host, "port": 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=600,
    )
    
    logger.info("Upload new index to OSS")
    print(
        "index prefix [" + index_prefix + "]\n"
        "embedding field names [" + '_'.join(embedding_field_names) + "]"
    )
    upload_data_oss(df, oss_client, embedding_field_names, embedding_sizes, index_prefix)