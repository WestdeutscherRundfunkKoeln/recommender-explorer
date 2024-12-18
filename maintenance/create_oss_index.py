import json
import sys
import os
from envyaml import EnvYAML
from datetime import datetime
import pandas as pd
from opensearchpy import OpenSearch, RequestsHttpConnection, helpers
import itertools
import boto3
import logging
import datetime

from tqdm import tqdm
from hashlib import sha256
from oss_utils import ModelConfig, Embedder, safe_value, get_approx_knn_mapping

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

SAMPLE_SIZE = 10000

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
    df["embedText"] = df["title"] + ". " + df["description"]
    df["embedTextHash"] = [
        sha256(text.encode("utf-8")).hexdigest() for text in df["embedText"]
    ]

    df["subgenreCategoriesIds"] = df["subgenreCategoriesId"]
    df["thematicCategoriesIds"] = df["thematicCategoriesId"]
    df["subgenreCategories"] = df["subgenreCategoriesTitle"]
    df["thematicCategories"] = df["thematicCategoriesTitle"]

    # load and process show luts
    transposed = []
    for index, row in df.iterrows():

        show_luts = {}
        show_core_id = row.get('showCrid', False)
        prim_id = row.id

        if not show_core_id:
            continue

        curr_episode_nr = row.get('episodeNumber', 10000)
        curr_season_nr = row.get('seasonNumber', 10000)

        if not show_luts.get(show_core_id):
            show_luts[show_core_id] = {}
            show_luts[show_core_id] = {'episode': prim_id}

        if curr_season_nr <= show_luts[show_core_id].get('season_nr', 10000):
            if curr_episode_nr < show_luts[show_core_id].get('episode_nr', 10000):
                # new low of season and episode
                show_luts[show_core_id] = {'episode': prim_id, 'season_nr': curr_season_nr,
                                           'episode_nr': curr_episode_nr}

        for idx, val in show_luts.items():
            item = {
                'id': idx,
                'episode': val.get('episode'),
                'season': val.get('season_nr', 0),
                'episode_nr': val.get('episode_nr', 0)
            }
            transposed.append(item)

    show_df = pd.DataFrame(transposed)
    return df, show_df

def calc_embeddings(df, model_names):

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

    if "isChildContent" in df.columns:
        df["isChildContent"] = df["isChildContent"].fillna(0).astype('bool')
    if "fskAgeRating" in df.columns:
        df["fskAgeRating"] = df["fskAgeRating"].fillna(0).astype('bool')
    if "isFamilyFriendly" in df.columns:
        df["isFamilyFriendly"] = df["isFamilyFriendly"].fillna(0).astype('bool')
    if "targetAudienceMinAge" in df.columns:
        df["targetAudienceMinAge"] = df["targetAudienceMinAge"].fillna(0).astype('bool')
    if "targetAudienceMaxAge" in df.columns:
        df["targetAudienceMaxAge"] = df["targetAudienceMaxAge"].fillna(0).astype('bool')



    if "editorialCategories" in df.columns:
        df["editorialCategories"].fillna('n/a', inplace=True)

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
        print("Indexing [" + document.get('id') + ']')
        if not document.get('id'):
            continue
        yield {
            "_index": index_name,
            "_type": "_doc",
            "_id": f"{document['id']}",
            "_source": filterKeys(document, keys),
        }
    # raise StopIteration
    
def upload_show_luts(df, client, target_idx):

    # transfer all columns, we could subset here
    use_these_keys = df.columns.tolist()

    # Set total number of documents
    number_of_docs = df.shape[0]
    successes = 0

    progress = tqdm(unit="docs", total=number_of_docs,
                    leave=True, desc="indexing")

    for ok, action in helpers.streaming_bulk(
        client=client,
        index=target_idx,
        actions=doc_generator(df, target_idx, use_these_keys),
    ):
        progress.update(1)
        successes += ok

    logger.info("Indexed [" + str(successes) + '] show documents')

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

    print("using: " + ','.join(use_these_keys))

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

    return target_idx_name

        
if __name__ == "__main__":

    if not len(sys.argv[1:]):
        exit("You must provide a configuration file for indexing")

    configuration_file_name = sys.argv[1:][0].removeprefix('config=')
    config = EnvYAML(configuration_file_name)
    indexing_sources = config['indexing_sources']
    c2c_models = indexing_sources['models_to_index']

    index_sample = os.environ.get('INDEX_SAMPLE') == 'True'
    index_prefix = os.environ.get('INDEX_PREFIX')

    logger.info(f"Index sample: {index_sample}")
    logger.info(f"Index prefix: {index_prefix}")


    host = os.environ.get('OPENSEARCH_HOST')
    auth = (os.environ.get('OPENSEARCH_USER'),
            os.environ.get('OPENSEARCH_PASS'))

    logger.info('Host: ' + host)

    logger.info("Preprocess data")
    df, show_df = load_and_preprocess_data(
        indexing_sources['base_data_bucket'],
        indexing_sources['base_data_file'],
        indexing_sources['subgenre_lut_file'],
        indexing_sources['thematic_lut_file'],
        index_sample
    )

    logger.info("Calculate embeddings")
    df, embedding_field_names, embedding_sizes = calc_embeddings(df, c2c_models)

    logger.info("Postprocess data")
    df = postprocess_data(df)

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

    target_idx = upload_data_oss(df, oss_client, embedding_field_names, embedding_sizes, index_prefix)
    logger.info("Upload show luts to OSS idx [" + target_idx + ']')
    show_df = show_df[show_df['id'].notna()]
    upload_show_luts(show_df, oss_client, target_idx)
    logger.info("All done and finished")