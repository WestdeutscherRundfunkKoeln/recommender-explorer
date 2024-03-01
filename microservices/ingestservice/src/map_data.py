from envyaml import EnvYAML
from dto.recoexplorer_item import RecoExplorerItem
import logging
import json
import pyjq
# import jq

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


class DataMapper:

    def __init__(self, config):
        mapping_definition_file = config['mapping_definition_file']
        mapping_file = EnvYAML(mapping_definition_file)
        self.mapping = mapping_file['mapping']

    def map_data(self, data) -> RecoExplorerItem: # input = entity
        mapped_data = pyjq.one(self.mapping, data)
        logger.info('Mapped data: ' + json.dumps(mapped_data, indent=4, default=str))
        response = RecoExplorerItem.model_validate(mapped_data)
        return response
