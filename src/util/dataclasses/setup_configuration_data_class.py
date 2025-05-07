from dataclasses import dataclass
from typing import Any

from src.util.dataclasses.model_configuration_data_class import ModelConfiguration
from src.util.dataclasses.opensearch_configuration_data_class import OpenSearchConfiguration


@dataclass
class SetupConfiguration:
    model_config: ModelConfiguration
    open_search_config: OpenSearchConfiguration

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'SetupConfiguration':
        return cls(
            model_config=ModelConfiguration.from_dict(data),
            open_search_config=OpenSearchConfiguration.from_dict(data)
        )

    def to_dict(self) -> dict[str, Any]:
        result = {}
        result.update(self.model_config.to_dict())
        result.update(self.open_search_config.to_dict())
        return result