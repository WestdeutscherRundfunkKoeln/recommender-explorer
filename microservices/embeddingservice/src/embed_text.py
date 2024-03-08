import logging
import json
from envyaml import EnvYAML
from sentence_transformers import SentenceTransformer
from pathvalidate import sanitize_filename
from hashlib import sha256

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


class EmbedText:

    def __init__(self, config):
        self.config = config
        # self.model_name = config['models']['model1']
        # self.model = SentenceTransformer(self.model_name)

    def embed_text(self, id, embed_text):
        self.model_name = self.config['models'][0]
        self.model = SentenceTransformer(self.model_name)
        hash = sha256(embed_text.encode('utf-8')).hexdigest()
        embedding = self.model.encode(embed_text).tolist()

        response = {'id': id, 'embedded_text': embed_text, 'hash': hash, 'embedding': embedding}

        logger.info('Response: ' + json.dumps(response, indent=4, default=str))

        return response
