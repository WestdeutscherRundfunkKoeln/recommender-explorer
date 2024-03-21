from envyaml import EnvYAML
from dto.recoexplorer_item import RecoExplorerItem
import logging
import json
import pyjq

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


class DataMapper:

    def __init__(self, config):
        self.mapping = config['mapping_definition']

    def map_data(self, data) -> RecoExplorerItem: # input = entity
        mapped_data = pyjq.one(self.mapping, data)
        logger.info('Mapped data: ' + json.dumps(mapped_data, indent=4, default=str))
        response = RecoExplorerItem.model_validate(mapped_data)
        return response
