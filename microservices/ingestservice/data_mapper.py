from envyaml import EnvYAML
from microservices.ingestservice.dto.media_data import MediaData
from microservices.ingestservice.dto.sophora_data import SophoraData
from microservices.ingestservice.dto.recoexplorer_item import RecoExplorerItem
import logging
import json

logger = logging.getLogger(__name__)


class DataMapper:

    def __init__(self):
        self.config_mapping = EnvYAML('microservices/ingestservice/config_wdr.yaml') # THIS HAS TO BE CHANGED

    def map_data(self, data: SophoraData) -> RecoExplorerItem: # input = entity
        mapped_data = {}
        for item in data:
            if item[0] in self.config_mapping['opensearch']['mapping']:
                mapped_key = self.config_mapping['opensearch']['mapping'][item[0]]
                if item[0] in self.config_mapping['opensearch']['restructuring']:
                    dict_key = self.config_mapping['opensearch']['restructuring'][item[0]]
                    mapped_data[mapped_key] = item[1][dict_key]
                else:
                    mapped_data[mapped_key] = item[1]
            else:
                mapped_data[item[0]] = item[1]
        logger.error(json.dumps(mapped_data, indent=4, default=str))
        response = RecoExplorerItem.model_validate(mapped_data)
        return response
