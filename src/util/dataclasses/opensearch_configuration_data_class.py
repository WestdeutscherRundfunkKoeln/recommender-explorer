from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class OpenSearchConfiguration:
    index: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'OpenSearchConfiguration':
        if 'opensearch' in data and isinstance(data['opensearch'], dict):
            return cls(
                index=data['opensearch'].get('index')
            )
        return cls()

    def to_dict(self) -> dict[str, Any]:
        result = {}
        if self.index is not None:
            result['opensearch'] = {
                'index': self.index
            }
        return result