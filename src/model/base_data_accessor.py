from abc import ABC, abstractmethod
from typing import Collection

from dto.item import ItemDto


class BaseDataAccessor(ABC):
    @abstractmethod
    def get_items_by_ids(self, item: ItemDto, ids: Collection[str]) -> list[ItemDto]:
        pass

    @abstractmethod
    def get_primary_key_by_field(self, item_ident, field):
        pass

    @abstractmethod
    def get_unique_vals_for_column(self, column, sort=True):
        pass

