from envyaml import EnvYAML
from microservices.ingestservice.dto.media_data import MediaData
from microservices.ingestservice.dto.sophora_data import SophoraData
from microservices.ingestservice.dto.recoexplorer_item import RecoExplorerItem
import logging
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

class DataMapper:

    def __init__(self):
        pass

    def map_data(self, config, data: SophoraData) -> RecoExplorerItem: # input = entity
        mapped_data = {}
        for item in data:
            if item[0] in config['opensearch']['mapping']:
                mapped_key = config['opensearch']['mapping'][item[0]]
                if item[0] in config['opensearch']['restructuring']:
                    dict_key = config['opensearch']['restructuring'][item[0]]
                    mapped_data[mapped_key] = item[1][dict_key]
                else:
                    mapped_data[mapped_key] = item[1]
            else:
                mapped_data[item[0]] = item[1]

        logger.info('Mapped data: ' + json.dumps(mapped_data, indent=4, default=str))
        response = RecoExplorerItem.model_validate(mapped_data)
        return response
