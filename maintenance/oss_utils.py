from sentence_transformers import SentenceTransformer
from pathvalidate import sanitize_filename
from tqdm import tqdm
from hashlib import sha256
import numpy as np
import pandas as pd


class ModelConfig():
    def __init__(self, 
                 model_prefix: str = '', 
                 model_name: str = 'sentence-transformers/distiluse-base-multilingual-cased-v1', 
                 include_title: bool = True, 
                 include_description: bool = True, 
                 include_keywords: bool = True):
        self._include_title = include_title
        self._include_description = include_description
        self._include_keywords = include_keywords
        self._model_name = model_name
        self._model_prefix = model_prefix

    def getConfigDict(self):
        config = {}
        config['model_name'] = self._model_name
        config['include_title'] = self._include_title
        config['include_description'] = self._include_description
        config['include_keywords'] = self._include_keywords

        return config

    def getStr(self) -> str:
        if self._model_prefix is not None:
            raw_filename = self._model_prefix + '_'
        else:
            raw_filename = ''

        raw_filename += self._model_name
        filename = sanitize_filename(raw_filename)

        if self._include_title:
            title = '_title'
        else:
            title = '_notitle'

        if self._include_description:
            desc = '_desc'
        else:
            desc = '_nodesc'

        if self._include_keywords:
            keywords = '_keywords'
        else:
            keywords = '_nokeywords'

        str_repr = filename+title+desc+keywords
        return str_repr

    def __str__(self):
        return self.getStr()


class Embedder():
    def __init__(self, model_config):
        self._config = model_config
        self._model = SentenceTransformer(self._config._model_name)

    def __getTextToEmbed(self, item) -> str:
        text = ""
        if self._config._include_title is True:
            text = item['title']+'. '
        if self._config._include_description:
            text += item['description']+'. '
        if self._config._include_keywords:
            keywords = '. '.join(item['keywords'])
            text += keywords
        return text

    def getConfig(self) -> ModelConfig:
        return self._config

    def calculate_embedding(self, item):
        id = item['id']
        embedded_text = self.__getTextToEmbed(item)
        hash = sha256(embedded_text.encode('utf-8')).hexdigest()
        embedding = self._model.encode(embedded_text).tolist()

        return {'id': id, 'embedded_text': embedded_text, 'hash': hash, 'embedding': embedding}

    def calulate_data_embeddings(self, dataset):
        cached_embeddings = {}
        num_items = len(dataset)
        print(num_items)
        for i in tqdm(range(num_items), position=0, leave=False, desc='Items in model'):
            res = self.calculate_embedding(dataset.iloc[i])
            cached_embeddings[res['id']] = res
        result = {}
        result['config'] = self._config.getConfigDict()
        result['embeddings'] = cached_embeddings

        return result

    
def get_approx_knn_mapping_by_size(emb_size):
    retval = {
        "type": "knn_vector",
                "dimension": emb_size,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "nmslib",
                    "parameters": {"ef_construction": 128, "m": 24}
                }
    }
    return retval


def get_approx_knn_mapping(fieldnames, emb_sizes):
    retval = {
        "settings": {
            "index": {"knn": True, "knn.algo_param.ef_search": 100, "number_of_shards": 2}
        },
        "mappings": {
            "properties": {}
        }
    }
    
    for i in range(len(fieldnames)):
        retval["mappings"]["properties"][fieldnames[i]
                                         ] = get_approx_knn_mapping_by_size(emb_sizes[i])
    return retval


def safe_value(field_val):
    if np.ndim(field_val) != 0:  # list arrray..
        return field_val if not pd.isna(field_val).all else "n/a"
    else:  #
        return field_val if not pd.isna(field_val) else "n/a"
    