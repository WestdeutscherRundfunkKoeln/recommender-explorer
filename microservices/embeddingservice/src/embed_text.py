import logging
import json
from sentence_transformers import SentenceTransformer
from hashlib import sha256
import os
import httpx

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

URL_SEARCH_SINGLE = os.environ.get("URL_SEARCH_SINGLE")

class EmbedText:

    def __init__(self, config):
        self.config = config

    def embed_text(self, id, embed_text):
        hash = sha256(embed_text.encode('utf-8')).hexdigest()
        response = {'id': id, 'embedTextHash': hash}

        for model in self.config['models']:
            for model_name, model_path in model.items():
                self.model = SentenceTransformer(model_path)
                embedding = self.model.encode(embed_text).tolist()
                response[model_name] = embedding

        logger.info('Response: ' + json.dumps(response, indent=4, default=str))

        # Send request to search service to add embedding to index
        httpx.post(url=URL_SEARCH_SINGLE, json=response).json()

        return response
