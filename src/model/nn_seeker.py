from abc import ABC, abstractmethod
from typing import Any

from dto.item import ItemDto


class NnSeeker(ABC):
    @property
    def ITEM_IDENTIFIER_PROP(cls):
        pass

    @abstractmethod
    def get_k_NN(
        self, item: ItemDto, k: int, nn_filter: dict[str, Any]
    ) -> tuple[list[str], list, str]: ...

    @abstractmethod
    def get_max_num_neighbours(self, content_idx) -> int: ...

    @abstractmethod
    def set_model_config(self, model_config): ...
