from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ItemDto(ABC):
    _position: str
    _item_type: str
    _provenance: str

    @abstractmethod
    def viewer(self) -> str:
        pass

    @property
    def provenance(self) -> str:
        return self._provenance

    @provenance.setter
    def provenance(self, v) -> None:
        self._provenance = v

    @property
    def position(self) -> str:
        return self._position

    @position.setter
    def position(self, v) -> None:
        self._position = v

    @property
    def item_type(self) -> str:
        return self._item_type

    @item_type.setter
    def item_type(self, v) -> None:
        self._item_type = v
